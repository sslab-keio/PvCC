#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#define BUF_SIZE 512
#define END_MSG "END"
#define EXIT_MSG "EXIT"
#define SET_CMD "SET"

#define PORT_NUM 7777
#define VM_NUM 4
#define WEIGHT_PER_PCPU 256
#define NORMAL_POOL "be"
#define DPDK_POOL "ls"
#define TSLICE 100
#define USE_VCPU_MIGRATE 0

int vm_weights[VM_NUM + 1];
int total_weight = 0;

int pvcc_sched(char buf[BUF_SIZE]);
int set_dpcpu(int dpcpu_num);
int set_weight();
int is_power_two(int weight);
int exec_xl(char *argv[]);
int debug_printf(const char * format, ...);

int main() {
  int s, s2, recv_len, send_len, i, ret;
  struct sockaddr_in skt_from, skt_to;
  in_port_t port_from = PORT_NUM;
  socklen_t sktlen;
  char buf[BUF_SIZE];

  set_dpcpu(VM_NUM);
  for (i = 1; i <= VM_NUM; i++) {
    vm_weights[i] = WEIGHT_PER_PCPU;
    total_weight += WEIGHT_PER_PCPU;

    // xl cpupool-migrate domain DPDK_POOL
    {
      char arg_domain[BUF_SIZE];
      sprintf(arg_domain, "seastar%d", i);
      char *argv[] = {"xl", "cpupool-migrate", arg_domain, DPDK_POOL, NULL};
      if (exec_xl(argv)) {
        perror("exec_xl");
        return -1;
      }
    }
  }

  // xl sched-credit -s -u TSLICE -r 0 -p DPDK_POOL
  {
    char arg_tslice[BUF_SIZE];
    sprintf(arg_tslice, "%d", TSLICE);
    char *argv[] = {"xl", "sched-credit", "-s", "-u", arg_tslice, "-r", "0", "-p", DPDK_POOL, NULL};
    if (exec_xl(argv)) {
      perror("exec_xl");
      return -1;
    }
  }

  memset(&skt_from, 0, sizeof skt_from);
  memset(&skt_to, 0, sizeof skt_to);
  skt_from.sin_port = htons(port_from);
  skt_from.sin_family = AF_INET;
  skt_from.sin_addr.s_addr = INADDR_ANY;

  if ((s = socket(PF_INET, SOCK_STREAM, 0)) < 0) {
    perror("socket");
    exit(1);
  }

  if (bind(s, (struct sockaddr *)&skt_from, sizeof skt_from) < 0) {
    perror("bind");
    exit(1);
  }

  if (listen(s, 5) < 0) {
    perror("listen");
    exit(1);
  }

  for (;;) {
    sktlen = sizeof skt_to;
    debug_printf("accept waiting...\n");
    if ((s2 = accept(s, (struct sockaddr *)&skt_to, &sktlen)) < 0) {
      perror("accept");
      exit(1);
    }
    debug_printf("accept connect from %s:%d\n", inet_ntoa(skt_to.sin_addr), ntohs(skt_to.sin_port));

    for (;;) {
      debug_printf("recv waiting...\n");
      if ((recv_len = recv(s2, buf, sizeof buf - 1, 0)) < 0) {
        perror("recv");
        exit(1);
      }
      buf[recv_len] = '\0';
      debug_printf("recv: '%s'(%d) from %s:%d\n", buf, recv_len, inet_ntoa(skt_to.sin_addr), ntohs(skt_to.sin_port));

      ret = pvcc_sched(buf);

      if (ret) {
        send_len = 3;
        if ((send_len = send(s2, "NG\n", send_len, 0)) < 0) {
          perror("send");
          exit(1);
        }
      } else {
        send_len = 3;
        if ((send_len = send(s2, "OK\n", send_len, 0)) < 0) {
          perror("send");
          exit(1);
        }
      }

      if (strncmp(buf, END_MSG, 3) == 0) {
        debug_printf("END...\n");
        break;
      }

      if (strncmp(buf, EXIT_MSG, 4) == 0) {
        debug_printf("EXIT...\n");
        break;
      }
    }
    close(s2);
    if (strncmp(buf, EXIT_MSG, 4) == 0) {
      debug_printf("EXIT2...\n");
      break;
    }
  }
  close(s);

  for (i = 1; i <= VM_NUM; i++) {
    set_weight(i, WEIGHT_PER_PCPU);
    // xl cpupool-migrate domain NORMAL_POOL
    {
      char arg_domain[BUF_SIZE];
      sprintf(arg_domain, "seastar%d", i);
      char *argv1[] = {"xl", "cpupool-migrate", arg_domain, NORMAL_POOL, NULL};
      if (exec_xl(argv1)) {
        perror("exec_xl");
        return -1;
      }
    }
  }
  set_dpcpu(0);

  return 0;
}

int pvcc_sched(char buf[BUF_SIZE]) {
  if (strncmp(buf, SET_CMD, 3) == 0) {
    int vm_num, weight;
    int ret;
    if (sscanf(&buf[3], "%d%d", &vm_num, &weight) < 0) {
      perror("sscanf");
      return -1;
    }
    debug_printf("SET %d %d\n", vm_num, weight);
    ret = set_weight(vm_num, weight);
    if (ret)
      return -1;
    return 0;
  } else if (strncmp(buf, END_MSG, 3) == 0 || strncmp(buf, EXIT_MSG, 4)) {
    return 0;
  } else {
    fprintf(stderr, "Invalid cmd\n");
    return -1;
  }
}

int set_dpcpu(int dpcpu_num) {
  static int cur_dpcpu_num = 0;
  int start_cpu, end_cpu;
  char *pool_to, *pool_from;

  // scale up
  if (dpcpu_num < 0) {
    fprintf(stderr, "dpcpu_num should be >= 0\n");
    return -1;
  } else if (dpcpu_num == cur_dpcpu_num) {
    // unchanged
    return 0;
  } else if (dpcpu_num > cur_dpcpu_num) { // scale up
    debug_printf("scale up %d -> %d\n", cur_dpcpu_num, dpcpu_num);
    start_cpu = cur_dpcpu_num + 1;
    end_cpu = dpcpu_num;
    pool_from = NORMAL_POOL;
    pool_to = DPDK_POOL;
  } else { // scale down
    debug_printf("scale down %d -> %d\n", cur_dpcpu_num, dpcpu_num);
    start_cpu = dpcpu_num + 1;
    end_cpu = cur_dpcpu_num;
    pool_from = DPDK_POOL;
    pool_to = NORMAL_POOL;
  }

  {
    char arg_cpunr[BUF_SIZE];
    sprintf(arg_cpunr, "%d-%d", start_cpu, end_cpu);
    // xl cpupool-cpu-remove pool_from start_cpu-end_cpu
    {
      char *argv[] = {"xl", "cpupool-cpu-remove", pool_from, arg_cpunr, NULL};
      if (exec_xl(argv)) {
        perror("exec_xl");
        return -1;
      }
    }

    // xl cpupool-cpu-remove pool_from start_cpu-end_cpu
    {
      char *argv[] = {"xl", "cpupool-cpu-add", pool_to, arg_cpunr, NULL};
      if (exec_xl(argv)) {
        perror("exec_xl");
        return -1;
      }
    }
  }

  cur_dpcpu_num = dpcpu_num;
  return 0;
}

int set_weight(int vm_num, int weight) {
  int cap, new_dpcpu_num;

  if (vm_num < 1 || VM_NUM < vm_num) {
    fprintf(stderr, "Invalid vm_num %d\n", vm_num);
    return -1;
  }
  if (is_power_two(weight) <= 0) {
    fprintf(stderr, "Invalid weight %d\n", weight);
    return -1;
  }
  cap = 100 * weight / WEIGHT_PER_PCPU;

  // xl sched-credit -d vm{vm_num} -w {weight}
  {
    char arg_domain[BUF_SIZE];
    char arg_weight[BUF_SIZE];
    char arg_cap[BUF_SIZE];
    char *argv[] = {"xl", "sched-credit", "-d", arg_domain, "-w", arg_weight, NULL};
    // char *argv[] = {"xl", "sched-credit", "-d", arg_domain, "-w", arg_weight, "-c", arg_cap, NULL};
    sprintf(arg_domain, "seastar%d", vm_num);
    sprintf(arg_weight, "%d", weight);
    sprintf(arg_cap, "%d", cap);
    if (exec_xl(argv)) {
      perror("exec_xl");
      return -1;
    }
  }

  total_weight += weight - vm_weights[vm_num];
  vm_weights[vm_num] = weight;

  new_dpcpu_num = (total_weight + WEIGHT_PER_PCPU - 1) / WEIGHT_PER_PCPU;
  if (new_dpcpu_num != 0)
    set_dpcpu(new_dpcpu_num);

  return 0;
}

int is_power_two(int weight) {
  int ret = 0;
  while (weight > 1) {
    if (weight % 2 != 0) {
      return -1;
    }
    weight /= 2;
    ret++;
  }
  return ret;
}

int exec_xl(char *argv[]) {
  int status;
  pid_t pid;
  pid = fork();
  if (pid == 0) {
    execvp("xl", argv);
    exit(1);
  } else {
    debug_printf("%s %s: ", argv[0], argv[1]);
    // printf("wait...\n");
    wait(&status);
    debug_printf("Exit Status %d\n", WEXITSTATUS(status));
    return WEXITSTATUS(status);
  }
}

int debug_printf(const char * format, ...) {
  va_list args;
  va_start(args, format);
#ifdef DEBUG
  return vprintf(format, args);
#endif
  va_end(args);
  return 0;
}
