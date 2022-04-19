FROM public.ecr.aws/m5j1b6u0/zinc:latest AS builder

FROM ubuntu:latest
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
