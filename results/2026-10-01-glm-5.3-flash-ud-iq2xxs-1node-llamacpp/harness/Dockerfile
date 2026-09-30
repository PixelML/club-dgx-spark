FROM nvidia/cuda:13.0.1-devel-ubuntu24.04 AS build
RUN apt-get update && apt-get install -y git cmake build-essential libcurl4-openssl-dev libssl-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth 1 -b glm5next/upstream https://github.com/unslothai/llama.cpp.git . && git log -1 --format=%H > /src/REV
RUN ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1; \
    export LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LD_LIBRARY_PATH LIBRARY_PATH=/usr/local/cuda/lib64/stubs && \
    cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="121" -DGGML_NATIVE=OFF -DLLAMA_BUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --target llama-server llama-bench -j 20
FROM nvidia/cuda:13.0.1-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y libcurl4 libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/ /app/
COPY --from=build /src/REV /app/REV
ENV LD_LIBRARY_PATH=/app
ENTRYPOINT ["/app/llama-server"]
