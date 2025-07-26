FROM ollama/ollama AS ollama

FROM cgr.dev/chainguard/wolfi-base

RUN apk add --no-cache libstdc++

COPY --from=ollama /usr/bin/ollama /usr/bin/ollama
COPY --from=ollama /usr/lib/ollama /usr/lib/ollama

RUN /usr/bin/ollama serve & sleep 5 && \
      /usr/bin/ollama pull llama3.2 && \
      /usr/bin/ollama pull llava && \
      /usr/bin/ollama pull all-minilm

# Environment variable setup
ENV OLLAMA_HOST=0.0.0.0

# Expose port for the service
EXPOSE 11434

ENTRYPOINT ["/usr/bin/ollama"]
CMD ["serve"]
