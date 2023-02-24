FROM public.ecr.aws/zinclabs/zinc:0.4.1@sha256:f9d2d939ca6f444ab9bfc3b4c298b57614aeecc8f8982160602e3480a6e1a032 AS builder

FROM ubuntu:latest@sha256:9a0bdde4188b896a372804be2384015e90e3f84906b750c1a53539b585fbbe7f
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
