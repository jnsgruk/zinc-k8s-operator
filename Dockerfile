FROM public.ecr.aws/h9e2j3o7/zinc:0.1.9 AS builder

FROM ubuntu:latest
COPY --from=builder /go/bin/zinc /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
