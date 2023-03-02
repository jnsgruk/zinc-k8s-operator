FROM public.ecr.aws/zinclabs/zinc:0.4.1@sha256:f9d2d939ca6f444ab9bfc3b4c298b57614aeecc8f8982160602e3480a6e1a032 AS builder

FROM ubuntu:latest@sha256:2adf22367284330af9f832ffefb717c78239f6251d9d0f58de50b86229ed1427
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
