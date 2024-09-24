CC=gcc
CFLAGS=-DDEBUG
BUILDDIR=build
TARGETS=$(BUILDDIR)/pvccsrv
SRCS=pvccsrv.c
OBJS=$(BUILDDIR)/pvccsrv.o

.PHONY: all clean
all: $(BUILDDIR) $(TARGETS)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(TARGETS): $(OBJS)
	$(CC) -o $@ $^

$(OBJS): $(SRCS)
	$(CC) -c $(CFLAGS) -o $@ $^

clean:
	rm -r $(BUILDDIR)
