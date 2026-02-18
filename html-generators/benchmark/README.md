# Generator Benchmarks

Performance comparison of execution methods for the HTML generator, measured on 95 snippets across 10 categories.

## Phase 1: Training / Build Cost (one-time)

These are one-time setup costs, comparable across languages.

| Step | Time | What it does |
|------|------|-------------|
| Python first run | 2.34s | Interprets source, creates `__pycache__` bytecode |
| JBang export | 2.92s | Compiles source + bundles dependencies into fat JAR |
| AOT training run | 3.14s | Runs JAR once to record class loading, produces `.aot` cache |

## Phase 2: Steady-State Execution (avg of 5 runs)

After one-time setup, these are the per-run execution times.

| Method | Avg Time | Notes |
|--------|---------|-------|
| **Fat JAR + AOT** | **0.35s** | Fastest; pre-loaded classes from AOT cache |
| **Fat JAR** | 0.50s | JVM class loading on every run |
| **JBang** | 1.19s | Includes JBang launcher overhead |
| **Python** | 1.37s | Uses cached `__pycache__` bytecode |

## How It Works

- **Python** caches compiled bytecode in `__pycache__/` after the first run, similar to how Java's AOT cache works.
- **Java AOT** (JEP 483) snapshots ~3,300 pre-loaded classes from a training run into a `.aot` file, eliminating class loading overhead on subsequent runs.
- **JBang** compiles and caches internally but adds launcher overhead on every invocation.
- **Fat JAR** (`java -jar`) loads and links all classes from scratch each time.

## AOT Cache Setup

```bash
# One-time: build the fat JAR
jbang export fatjar --force --output html-generators/generate.jar html-generators/generate.java

# One-time: build the AOT cache (~21 MB, platform-specific)
java -XX:AOTCacheOutput=html-generators/generate.aot -jar html-generators/generate.jar

# Steady-state: run with AOT cache
java -XX:AOTCache=html-generators/generate.aot -jar html-generators/generate.jar
```

## Environment

| | |
|---|---|
| **CPU** | Apple M1 Max |
| **RAM** | 32 GB |
| **Java** | OpenJDK 25.0.1 (Temurin) |
| **JBang** | 0.136.0 |
| **Python** | 3.14.3 |
| **OS** | Darwin |

## Reproduce

```bash
./html-generators/benchmark/run.sh            # print results to stdout
./html-generators/benchmark/run.sh --update    # also update this file
```
