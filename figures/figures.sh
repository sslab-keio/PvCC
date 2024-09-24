#!/bin/bash
set -euxo pipefail

# sudo docker compose run --rm graph python3 /scripts/fig02.py
# sudo docker compose run --rm graph python3 /scripts/fig06.py
# sudo docker compose run --rm graph python3 /scripts/fig10.py
# for i in {0..11}; do
for i in {15..17}; do
	# sudo docker compose run --rm graph python3 /scripts/fig11a.py ${i} &
	sudo docker compose run -T --rm graph python3 /scripts/fig11b.py ${i} &
	# sudo docker compose run --rm graph python3 /scripts/fig11c.py ${i} &
done


