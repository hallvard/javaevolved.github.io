# Generator Benchmarks

Performance comparison of execution methods for the HTML generator, measured on 95 snippets across 10 categories.

## CI Benchmark (GitHub Actions)

[![Benchmark Generator](https://github.com/javaevolved/javaevolved.github.io/actions/workflows/benchmark.yml/badge.svg)](https://github.com/javaevolved/javaevolved.github.io/actions/workflows/benchmark.yml)

The most important benchmark runs on GitHub Actions because it measures performance in the environment where the generator actually executes — CI. The [Benchmark Generator](https://github.com/javaevolved/javaevolved.github.io/actions/workflows/benchmark.yml) workflow is manually triggered and runs across **Ubuntu**, **Windows**, and **macOS**.

### Why CI benchmarks matter

On a developer machine, repeated runs benefit from warm OS file caches — the operating system keeps recently read files in RAM, making subsequent reads nearly instant. This masks real-world performance differences. Python also benefits from `__pycache__/` bytecode that persists between runs.

In CI, **every workflow run starts on a fresh runner**. There is no `__pycache__/`, no warm OS cache, no JBang compilation cache. This is the environment where the deploy workflow runs, so these numbers reflect actual production performance.

### How the CI benchmark works

The workflow has three jobs:

1. **`benchmark`** — Runs Phase 1 (training/build costs) and Phase 2 (steady-state execution) on each OS. All tools are installed in the same job, so this measures raw execution speed after setup.

2. **`build-jar`** — Builds the fat JAR and AOT cache on each OS, then uploads them as workflow artifacts. This simulates what the `build-generator.yml` workflow does weekly: produce the JAR and AOT cache and store them in the GitHub Actions cache.

3. **`ci-cold-start`** — The key benchmark. Runs on a **completely fresh runner** that has never executed Java or Python in the current job. It downloads the JAR and AOT artifacts (simulating the `actions/cache/restore` step in the deploy workflow), then measures a single cold run of each method. This is the closest simulation of what happens when the deploy workflow runs:
   - **Python** has no `__pycache__/` — it must interpret every `.py` file from scratch
   - **Fat JAR** must load and link all classes on a cold JVM
   - **Fat JAR + AOT** loads pre-linked classes from the `.aot` file, skipping class loading entirely

   The `setup-java` and `setup-python` actions are required to provide the runtimes, but they don't warm up the generator code. The first invocation of `java` or `python3` in this job is the benchmark measurement itself.

### Why Java AOT wins in CI

Java's AOT cache (JEP 483) snapshots the result of class loading and linking from a training run into a `.aot` file. This file is platform-specific and ~21 MB. When restored from the actions cache, the JVM skips the expensive class discovery, verification, and linking steps that normally happen on first run.

Python's `__pycache__/` serves a similar purpose — it caches compiled bytecode so Python doesn't re-parse `.py` files. But `__pycache__/` is not committed to git or stored in CI caches, so **Python always pays full interpretation cost in CI**. Java AOT, by contrast, is stored in the actions cache and restored before each deploy.

## Local Benchmark

The local benchmark script runs all three phases on your development machine. Local results will differ from CI because of OS file caching and warm `__pycache__/`.

### Phase 1: Training / Build Cost (one-time)

These are one-time setup costs, comparable across languages.

| Step | Time | What it does |
|------|------|-------------|
| Python first run | 1.98s | Interprets source, creates `__pycache__` bytecode |
| JBang export | 2.19s | Compiles source + bundles dependencies into fat JAR |
| AOT training run | 2.92s | Runs JAR once to record class loading, produces `.aot` cache |

### Phase 2: Steady-State Execution (avg of 5 runs)

After one-time setup, these are the per-run execution times.

| Method | Avg Time | Notes |
|--------|---------|-------|
| **Fat JAR + AOT** | **0.32s** | Fastest; pre-loaded classes from AOT cache |
| **Fat JAR** | 0.44s | JVM class loading on every run |
| **JBang** | 1.08s | Includes JBang launcher overhead |
| **Python** | 1.26s | Uses cached `__pycache__` bytecode |

### Phase 3: CI Cold Start (simulated locally)

Clears `__pycache__/` and JBang cache, then measures a single run. On a local machine the OS file cache still helps, so these numbers are faster than true CI.

| Method | Time | Notes |
|--------|------|-------|
| **Fat JAR + AOT** | **0.46s** | AOT cache ships pre-loaded classes |
| **Fat JAR** | 0.40s | JVM class loading from scratch |
| **JBang** | 3.25s | Must compile source before running |
| **Python** | 0.16s | No `__pycache__`; full interpretation |

### How each method works

- **Python** caches compiled bytecode in `__pycache__/` after the first run, similar to how Java's AOT cache works. But this cache is local-only and not available in CI.
- **Java AOT** (JEP 483) snapshots ~3,300 pre-loaded classes from a training run into a `.aot` file, eliminating class loading overhead on subsequent runs. The `.aot` file is stored in the GitHub Actions cache.
- **JBang** compiles and caches internally but adds launcher overhead on every invocation.
- **Fat JAR** (`java -jar`) loads and links all classes from scratch each time.

### AOT Cache Setup

```bash
# One-time: build the fat JAR
jbang export fatjar --force --output html-generators/generate.jar html-generators/generate.java

# One-time: build the AOT cache (~21 MB, platform-specific)
java -XX:AOTCacheOutput=html-generators/generate.aot -jar html-generators/generate.jar

# Steady-state: run with AOT cache
java -XX:AOTCache=html-generators/generate.aot -jar html-generators/generate.jar
```

### Environment

| | |
|---|---|
| **CPU** | Apple M1 Max |
| **RAM** | 32 GB |
| **Java** | OpenJDK 25.0.1 (Temurin) |
| **JBang** | 0.136.0 |
| **Python** | 3.14.3 |
| **OS** | Darwin |

### Reproduce

```bash
./html-generators/benchmark/run.sh            # print results to stdout
./html-generators/benchmark/run.sh --update    # also update local results in this file
```
