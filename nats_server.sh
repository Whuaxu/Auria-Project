docker run -it --net=host \
      --rm \
      nats:latest \
      --addr=0.0.0.0 \
      --http_port 8222
