# Generator Benchmarks

Performance comparison of execution methods for the HTML generator, measured on 95 snippets across 10 categories.

## Phase 1: Training / Build Cost (one-time)

These are one-time setup costs, comparable across languages.

| Step | Time | What it does |
|------|------|-------------|
| Python first run | 1.98s | Interprets source, creates `__pycache__` bytecode |
| JBang export | 2.19s | Compiles source + bundles dependencies into fat JAR |
| AOT training run | 2.92s | Runs JAR once to record class loading, produces `.aot` cache |

## Phase 2: Steady-State Execution (avg of 5 runs)

After one-time setup, these are the per-run execution times.

| Method | Avg Time | Notes |
|--------|---------|-------|
| **Fat JAR + AOT** | **0.32s** | Fastest; pre-loaded classes from AOT cache |
| **Fat JAR** | 0.44s | JVM class loading on every run |
| **JBang** | 1.08s | Includes JBang launcher overhead |
| **Python** | 1.26s | Uses cached `__pycache__` bytecode |

## Phase 3: CI Cold Start (fresh runner, no caches)

Simulates a CI environment where every run is the first run.
Python has no `__pycache__`, JBang has no compilation cache.
Java AOT benefits from the pre-built `.aot` file restored from actions cache.

| Method | Time | Notes |
|--------|------|-------|
| **Fat JAR + AOT** | **0.46s** | AOT cache ships pre-loaded classes |
| **Fat JAR** | 0.40s | JVM class loading from scratch |
| **JBang** | 3.25s | Must compile source before running |
| **Python** | 0.16s | No `__pycache__`; full interpretation |

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

### CI Benchmark

The [Benchmark Generator](https://github.com/javaevolved/javaevolved.github.io/actions/workflows/benchmark.yml) workflow runs cross-platform benchmarks (Ubuntu, Windows, macOS) on GitHub Actions. It includes a CI cold-start phase on a fresh runner to measure true first-run performance. Trigger it manually from the Actions tab.
