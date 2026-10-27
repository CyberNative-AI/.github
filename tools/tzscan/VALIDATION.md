# How tzscan was checked

Each row is one copy of the time-zone data in one image. **Expected** is the release established without tzscan, by the method in the last column (described below). **tzscan** is what `tzscan.py --json` reported for the same image digest. Checked 13–14 October 2026 on Linux x86-64.

A release written `<2026b` or `>=2026e` means the offsets only place the copy in that range. `absent` means the image has no zoneinfo tree, and tzscan must not report one.

Result: 65 of 65 rows match on 59 images. No row where the expected copy is stale was reported current.

| Image | Digest | Copy | Expected | tzscan | Method |
|---|---|---|---|---|---|
| `eclipse-temurin:8-jre` | `sha256:7806d0570e7234dccae4232e8273e87a0fcb74ca7c6f8692c9f5c672f355fd1d` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `eclipse-temurin:11-jre` | `sha256:ad419849e59e2c7a325078dff5eb64db6f61c8872e316dfd501031ed72efc2dd` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `eclipse-temurin:17-jre` | `sha256:cd97df8431db59b12c5ded535294c9b5fb6d9caddb85aeba703c2660ff20d0dc` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `eclipse-temurin:21-jre` | `sha256:dc9cf8ce05fab93643ec058491c3f0ab3cf65de8e11e7a8a999570364399f4a3` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `eclipse-temurin:25-jre` | `sha256:fcd7fd7b387f94bb2ac461478a7436ad8e349924c374ea8313919624dceae636` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `eclipse-temurin:25-jre` | `sha256:fcd7fd7b387f94bb2ac461478a7436ad8e349924c374ea8313919624dceae636` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `amazoncorretto:21` | `sha256:d965a0725293a57ea781ba3712d4f024f338aefa249af83b5c1f3981d0e21556` | jdk-tzdb `lib/tzdb.dat` | 2026d | 2026d | java |
| `amazoncorretto:25` | `sha256:06f99cdfd01c26ed2a5b03dc85385d36c17aa81ddfcaf8500f641ab556a985d6` | jdk-tzdb `lib/tzdb.dat` | 2026d | 2026d | java |
| `gcr.io/distroless/java21-debian13` | `sha256:903eb60cbfa13a9bb0156d398e65c7a9c5df755f0421452f4f4e3ae014955402` | jdk-tzdb `lib/tzdb.dat` | 2026b | 2026b | java |
| `gcr.io/distroless/java21-debian13` | `sha256:903eb60cbfa13a9bb0156d398e65c7a9c5df755f0421452f4f4e3ae014955402` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `registry.access.redhat.com/ubi9/openjdk-21-runtime` | `sha256:856ee6542b8fdf09a065fd5439309fc3f3c821fb8efac48aa6191c93635dd907` | jdk-tzdb `lib/tzdb.dat` | >=2026e | >=2026e | java |
| `registry.access.redhat.com/ubi9/openjdk-17-runtime` | `sha256:b65af124e0461fcdcae4cbb391ae827868d8fd01ca030a71c1c9eb2b42b01368` | jdk-tzdb `lib/tzdb.dat` | >=2026e | >=2026e | java |
| `php:8.5-cli` | `sha256:01a109229f4465bc9ef042d9198f09a4d9da7775a825dbd8572dcdbd8756c4d3` | timelib `usr/local/bin/php` | 2026c | 2026c | php |
| `php:8.4-cli` | `sha256:1d2cf2b7d715b5b3aa959f0150ccbcc7b71e0181b637e443abf40a7fb56bf79a` | timelib `usr/local/bin/php` | 2026c | 2026c | php |
| `php:8.4-cli` | `sha256:1d2cf2b7d715b5b3aa959f0150ccbcc7b71e0181b637e443abf40a7fb56bf79a` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `php:8.3-cli` | `sha256:aafe21201943a8a6e497ddfb471e2ce68ada76adede38c7d61fede8918b24319` | timelib `usr/local/bin/php` | <2026b | <2026b | php |
| `php:8.2-cli` | `sha256:118ef4fb1db5e866fb604f2f260da81f819a0a1eac87a4083f9194f48e00beee` | timelib `usr/local/bin/php` | <2026b | <2026b | php |
| `golang:1.26` | `sha256:d7722066f0b60ceccb6c0643cbed1f5f9e15506ac237146c95333504d7805d89` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | go |
| `golang:1.26` | `sha256:d7722066f0b60ceccb6c0643cbed1f5f9e15506ac237146c95333504d7805d89` | zoneinfo `lib/time/zoneinfo.zip` | <2026b | <2026b | go |
| `golang:1.25` | `sha256:699337d620559a59b4a2bb298ad59611e535d2ee755a34cf2d2a98f37578dc80` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | go |
| `golang:1.25` | `sha256:699337d620559a59b4a2bb298ad59611e535d2ee755a34cf2d2a98f37578dc80` | zoneinfo `lib/time/zoneinfo.zip` | <2026b | <2026b | go |
| `golang:1.27` | `sha256:007a316059246276cb214df93950be77837545dc78007a73e0291a4963d5d3bf` | zoneinfo `lib/time/zoneinfo.zip` | 2026c | 2026c | go |
| `gcr.io/distroless/static-debian12` | `sha256:d75cdd72874d4790092fcb1b058493ecf6bb5bf2b2b897045b00ff01d91843f2` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `gcr.io/distroless/static-debian13` | `sha256:58133991db06659feaabe0f4e97a35cebf15ef4ea08f8a4c6d2ee5f75e4aa6a0` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `debian:13` | `sha256:913f6706df59a68922d1dd08f78c2476560a8d367897200a6005b00e5f67c2d5` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `debian:12` | `sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `amazonlinux:2023` | `sha256:8ed3c0a996841537f75607e7d1de2114d8150391f75792e8da9268738547e73f` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `mcr.microsoft.com/dotnet/runtime-deps:8.0` | `sha256:c4e7603bcf65f6be5cc854ebd20d4cbe12bb70bb598fbd0486d35a9d828c1f41` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `mcr.microsoft.com/dotnet/runtime-deps:10.0` | `sha256:da5846024d0008b48259b53a8953d39381fe5b7ec99ef1449ba4ba927f201490` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `ruby:3.4-slim` | `sha256:c12225b6a73743f943530d9e610f4ae78e0dbcffdcf797b01522a55f7d25acb3` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `ubuntu:26.04` | `sha256:f144425ff09be612d6d9ad965196e9cdc23dae1f42110a8a11a3e9a8198759f7` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `ubuntu:24.04` | `sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `ubuntu:22.04` | `sha256:5ec03bb3441e8b0bf3b4f9cd4629a1ae763010dc3035bb8da3ae6cf026486401` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `alpine:3.22` | `sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `redhat/ubi9-minimal` | `sha256:c4c285d42941ebb2bd4da878479008e1e4536bb599aad1dbe568f89de9053661` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `redhat/ubi10-minimal` | `sha256:552f8cc1ddb0bc9e411065c78499aa4dbc2c4ea9bd057aa0e6e44940db13acb5` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |
| `registry.k8s.io/kube-controller-manager:v1.34.12` | `sha256:8a92c48d3faa0649598a4d854d294ff9d5de66bad5b23ddeb4c3b94c6bdcbf96` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `registry.k8s.io/kube-controller-manager:v1.35.9` | `sha256:d7e4983f79ee763f7c56226395ab9c55261ff6035df5ed23eef9bd26b63eb140` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `registry.k8s.io/kube-controller-manager:v1.36.5` | `sha256:2d717af134451db77ea053c3426bc82edc0e55415eb36e1260313c636ebe9a4d` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `registry.k8s.io/kube-controller-manager:v1.37.1` | `sha256:d470c1b85aebb466e971c06239cc6a31a4ac337a78600cef80375a79a1be1641` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `registry.k8s.io/build-image/go-runner:v2.4.0-go1.27.1-bookworm.0` | `sha256:9084b0e8021e26ed7d788c7c41fffc61cfc9cf2ab131fb04ed1cf3e630c2a87c` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `registry.k8s.io/build-image/go-runner:v2.4.0-go1.27.1-trixie.0` | `sha256:12de409998bf8280ae56fd776e09dbbafe5e67a87744fd9843363e244fbac875` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `mysql:8.4.10` | `sha256:8dbcf531a03aade657e181b9cf2f1d1803ce621a1d55610cb44cb531ab7d7db6` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `mysql:8.4.11` | `sha256:24989179f58856db763f418010c1169fecc944e3ec1ea7e921572d83eb070f70` | zoneinfo `usr/share/zoneinfo` | >=2026e | >=2026e | pkg |
| `mariadb:11.8` | `sha256:6422478cb8e159f080fb1d8ccf65101e26fe51385787fde7d16c3b165a331f15` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `mongo:9.0.2` | `sha256:f5c6240ae8fccc21cf75acc6462929b3394a7a5a7abd934b6b0e7ada5eb5fe95` | timelib `usr/bin/mongod` | <2026b | <2026b | mongo |
| `mongo:8.0` | `sha256:6657bf2413fefc5be649390318f5b4cd7328e982722f8ce2ac6dfa6f0a42cb03` | timelib `usr/bin/mongod` | <2026b | <2026b | mongo |
| `mongo:7.0` | `sha256:9650758f83af117fc96699f030a44f9300bed839734e67012f56df05b2fd6290` | timelib `usr/bin/mongod` | <2026b | <2026b | mongo |
| `docker.elastic.co/elasticsearch/elasticsearch:9.5.5` | `sha256:13b4a40bb095774f5fda635e45fd5677cc6a26565e42b24997b0c72b88e75984` | jdk-tzdb `jdk/lib/tzdb.dat` | 2026b | 2026b | es |
| `docker.elastic.co/elasticsearch/elasticsearch:8.19.23` | `sha256:4d0724bb8d78d7a2330693623e26ca4d621079d062ecc8a30b3e1fc180ec14c1` | jdk-tzdb `jdk/lib/tzdb.dat` | 2026b | 2026b | es |
| `opensearchproject/opensearch:3.9.0` | `sha256:adfa61f85025d06b4aeb562e7e74fde7e31c437039c93c3862c17e9acebd6c7c` | jdk-tzdb `jdk/lib/tzdb.dat` | 2026b | 2026b | es |
| `opensearchproject/opensearch:2.19.6` | `sha256:e321cb03c643874c42240458a618db56bc1e4fc143b10c41bec653542bc6851b` | jdk-tzdb `jdk/lib/tzdb.dat` | 2026a | 2026a | es |
| `trinodb/trino:483` | `sha256:db58cc93e593a2706553745f276bb119c9810e69918be56ecde088ba7ccb0534` | jdk-tzdb `lib/tzdb.dat` | 2026a | 2026a | trino |
| `trinodb/trino:483` | `sha256:db58cc93e593a2706553745f276bb119c9810e69918be56ecde088ba7ccb0534` | joda `usr/lib/trino/lib/joda-time*.jar` | 2026b | 2026b | trino |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:e5bc0bf2c7770f35c7e43f06a4ecb497a01f552afe14cc34526a183f8e30b0fd` | tzif-blobs `usr/bin/clickhouse` | >=2026e | >=2026e | clickhouse |
| `clickhouse/clickhouse-server:26.3.50.11` | `sha256:2cdf2cb1deff8364db9dde4f344bb139ca70bebfef0c9725cbd1360105ac58f4` | tzif-blobs `usr/bin/clickhouse` | >=2026e | >=2026e | clickhouse |
| `clickhouse/clickhouse-server:25.8.33.6` | `sha256:0152dd511befe6a2c2ef53e930726179669b08116da78500b37c51c96ff5ee77` | tzif-blobs `usr/bin/clickhouse` | <2026b | <2026b | clickhouse |
| `node:22.23.3` | `sha256:0e5f906573693feaa1e21057ebdcfdb5bd5021f050b2dc7c9deceb629c7da2a8` | icu `usr/local/bin/node` | 2026c | 2026c | node |
| `node:24` | `sha256:3d27e5c11e5786e309ec3e03f93ae536eb36e6e5eb3714d5eb3300a36157add0` | icu `usr/local/bin/node` | 2026c | 2026c | node |
| `node:24-slim` | `sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20` | icu `usr/local/bin/node` | 2026c | 2026c | node |
| `node:22-bookworm-slim` | `sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392` | icu `usr/local/bin/node` | 2026c | 2026c | node |
| `node:26.11.1-slim` | `sha256:193fe51b64e77981119c98c2002c9e32a70e2f006fb4d25068ce0558998917f0` | icu `usr/local/bin/node` | >=2026e | >=2026e | node |
| `python:3.12-slim` | `sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | python |
| `python:3.14-slim` | `sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | python |
| `python:3.15.0rc3-slim` | `sha256:a3af3d230522dd52f7f2191b39e1892912dbcb0c8dee22afdec3dc83baf0f549` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | python |

## arm64

The arm64 builds of 11 images above, from the same image index (the x86-64 digests above are index digests), pulled by their arm64 manifest digest and scanned on 27 October 2026 with `tzscan.py --json`, from an x86-64 host. All 11 gave the same verdicts, releases and exit status as their x86-64 build. `eclipse-temurin:21-jre` is a newer index than the one in the table above: its OS tzdata is now 2026e on both architectures.

**Expected** is filled in where the release was established on arm64, and all 17 match. **Run on arm64 under emulation** means the image's own arm64 binary, started with `qemu-aarch64` 10.2.1 user-mode emulation as the container's entrypoint, ran the probe from Methods below. The Java probe was compiled for Java 8, because a JRE cannot run a source file. **File identical** means the file has the same SHA-256 as the x86-64 copy measured above. For rows marked not established, the copy is inside a binary we did not run on arm64, or it is a file whose release we did not establish on either architecture. tzscan's verdict there equals its x86-64 verdict.

| Image | arm64 digest | Copy | Expected | tzscan | Method |
|---|---|---|---|---|---|
| `eclipse-temurin:21-jre` | `sha256:e8ffcc88eeec92a9860c5b574dfedfb9a7cef2a5cc7de8e4f2d029c7e8bbd2df` | jdk-tzdb `opt/java/openjdk/lib/tzdb.dat` | 2026b | 2026b | java, run on arm64 under emulation |
| `eclipse-temurin:21-jre` | `sha256:e8ffcc88eeec92a9860c5b574dfedfb9a7cef2a5cc7de8e4f2d029c7e8bbd2df` | zoneinfo `usr/share/zoneinfo` | >=2026e | >=2026e | pkg |
| `php:8.4-cli` | `sha256:3cbf9ac1eb9249e5c72dfd1976f7b1eff70936f4fbfd60475373d67e15bde5d4` | timelib `usr/local/bin/php` | 2026c | 2026c | php, run on arm64 under emulation |
| `php:8.4-cli` | `sha256:3cbf9ac1eb9249e5c72dfd1976f7b1eff70936f4fbfd60475373d67e15bde5d4` | timelib `usr/local/bin/php-cgi` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `php:8.4-cli` | `sha256:3cbf9ac1eb9249e5c72dfd1976f7b1eff70936f4fbfd60475373d67e15bde5d4` | timelib `usr/local/bin/phpdbg` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `php:8.4-cli` | `sha256:3cbf9ac1eb9249e5c72dfd1976f7b1eff70936f4fbfd60475373d67e15bde5d4` | timelib `usr/local/lib/libphp.so` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `php:8.4-cli` | `sha256:3cbf9ac1eb9249e5c72dfd1976f7b1eff70936f4fbfd60475373d67e15bde5d4` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `golang:1.27` | `sha256:a83e961ad968e2e7abc2a59554e356f00c2a270a15fbb39f2c84a4caf13be9c3` | zoneinfo `usr/local/go/lib/time/zoneinfo.zip` | 2026c | 2026c | file identical to the x86-64 copy, measured 2026c with go |
| `golang:1.27` | `sha256:a83e961ad968e2e7abc2a59554e356f00c2a270a15fbb39f2c84a4caf13be9c3` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `registry.k8s.io/kube-controller-manager:v1.36.5` | `sha256:15f8587dc75f4f473bcff3c514193f192924e1e087936556bec94b5c087a32c3` | go-embedded `usr/local/bin/kube-controller-manager` | — | <2026b | not established on arm64; same verdict as x86-64 |
| `registry.k8s.io/kube-controller-manager:v1.36.5` | `sha256:15f8587dc75f4f473bcff3c514193f192924e1e087936556bec94b5c087a32c3` | zoneinfo `usr/share/zoneinfo` | 2026b | 2026b | pkg |
| `node:24-slim` | `sha256:ba6b7d0ee561d9d49deb99e2b93c98632cc287b6cca1a6b18d66127054efa4dc` | icu `usr/local/bin/node` | 2026c | 2026c | node, run on arm64 under emulation |
| `node:24-slim` | `sha256:ba6b7d0ee561d9d49deb99e2b93c98632cc287b6cca1a6b18d66127054efa4dc` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `python:3.14-slim` | `sha256:7f47c8ffd4e70e88f7326b68e7df95109597ef66023a1052b7d1ec18390d2604` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg and python, run on arm64 under emulation |
| `trinodb/trino:483` | `sha256:aa18e61b2e7776ab8641ba8baaa8687d0430894e88c639e61010cc46a994ab36` | jdk-tzdb `lib/tzdb.dat` | 2026a | 2026a | java, run on arm64 under emulation |
| `trinodb/trino:483` | `sha256:aa18e61b2e7776ab8641ba8baaa8687d0430894e88c639e61010cc46a994ab36` | joda `usr/lib/trino/lib/joda-time_joda-time-2.14.2.jar` | 2026b | 2026b | file identical to the x86-64 copy, measured 2026b with trino |
| `trinodb/trino:483` | `sha256:aa18e61b2e7776ab8641ba8baaa8687d0430894e88c639e61010cc46a994ab36` | threetenbp `usr/lib/trino/plugin/bigquery/org.threeten_threetenbp-1.7.0.jar!/org/threeten/bp/TZDB.dat` | — | 2024b | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | tzif-blobs `usr/bin/clickhouse` | >=2026e | >=2026e | clickhouse, run on arm64 under emulation |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | icu `usr/bin/clickhouse` | — | 2025b | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | chrono-tz `usr/bin/clickhouse` | — | 2025b | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | chrono-tz `usr/bin/clickhouse` | — | <=2025b | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | icu `usr/share/zoneinfo-icu/44/be/zoneinfo64.res` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | icu `usr/share/zoneinfo-icu/44/le/zoneinfo64.res` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `clickhouse/clickhouse-server:26.9.18.11` | `sha256:eda2c8d431084bbeba793369e715f7bc96fc314f8543b27d81ce65b651ac18a7` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `mongo:8.0` | `sha256:f7b146ec8059a89b16b2290c8d6e27c2eebf16f8f8884e6d56c248a8770c6fd1` | timelib `usr/bin/mongod` | — | <2026b | not established on arm64; same verdict as x86-64 |
| `mongo:8.0` | `sha256:f7b146ec8059a89b16b2290c8d6e27c2eebf16f8f8884e6d56c248a8770c6fd1` | timelib `usr/bin/mongos` | — | <2026b | not established on arm64; same verdict as x86-64 |
| `mongo:8.0` | `sha256:f7b146ec8059a89b16b2290c8d6e27c2eebf16f8f8884e6d56c248a8770c6fd1` | icu `usr/bin/mongosh` | — | 2026c | not established on arm64; same verdict as x86-64 |
| `mongo:8.0` | `sha256:f7b146ec8059a89b16b2290c8d6e27c2eebf16f8f8884e6d56c248a8770c6fd1` | timelib `usr/lib/mongosh_crypt_v1.so` | — | <2026b | not established on arm64; same verdict as x86-64 |
| `mongo:8.0` | `sha256:f7b146ec8059a89b16b2290c8d6e27c2eebf16f8f8884e6d56c248a8770c6fd1` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `debian:13` | `sha256:b55910b579d6eb05ebd79fbc8468b974fa39bb0610d52e1f1390bb2177ab7614` | zoneinfo `usr/share/zoneinfo` | 2026c | 2026c | pkg |
| `alpine:3.22` | `sha256:2e1a7aa4cbc4e9e5222bb4c24a839aa1a6170ea5492d644777ce7b178824e44f` | zoneinfo `usr/share/zoneinfo` | absent | absent | none |

## Methods

The probes print offsets for 15 December 2026, 12:00 UTC, after the change. Correct values: Vancouver −7, Edmonton −6, Inuvik −6, Winnipeg −5. Where a probe includes Casablanca, it is checked at a date after 20 September 2026; correct is +0.

**java.** Run inside the image with its own `java` (`java Probe.java`; on Java 8, compile first). Prints the JDK's tz data version and the offsets from `java.time` and `java.util.TimeZone`.

```java
import java.time.*;
import java.time.zone.*;
public class Probe {
  public static void main(String[] a) {
    Instant t = Instant.parse("2026-12-15T12:00:00Z");
    StringBuilder sb = new StringBuilder();
    for (String z : new String[]{"America/Vancouver","America/Edmonton","America/Inuvik","America/Winnipeg"}) {
      sb.append(z).append('=').append(ZoneId.of(z).getRules().getOffset(t)).append(' ');
      // legacy API path too
      sb.append("legacy=").append(java.util.TimeZone.getTimeZone(z).getOffset(t.toEpochMilli())/3600000).append(' ');
    }
    System.out.println("java.version=" + System.getProperty("java.version") + " tzdb=" + ZoneRulesProvider.getVersions("UTC").keySet() + " " + sb);
  }
}
```

**php.** `php probe.php` inside the image; prints `timezone_version_get()` and the offsets from PHP's built-in database.

```php
<?php
$t = new DateTimeImmutable('2026-12-15T12:00:00Z');
echo 'php=', PHP_VERSION, ' timezonedb=', timezone_version_get(), ' ';
foreach (['America/Vancouver','America/Edmonton','America/Inuvik','America/Winnipeg'] as $z) {
  echo $z, '=', $t->setTimezone(new DateTimeZone($z))->format('P'), ' ';
}
echo "\n";
```

**go.** `probe.go` built with the image's Go toolchain and run three ways: with the image's `/usr/share/zoneinfo`; with `ZONEINFO=$(go env GOROOT)/lib/time/zoneinfo.zip`; and built with `-tags timetzdata` into a `scratch` image (no zoneinfo at all).

```go
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	t := time.Date(2026, 12, 15, 12, 0, 0, 0, time.UTC)
	fmt.Print(runtime.Version(), " ")
	for _, z := range []string{"America/Vancouver", "America/Edmonton", "America/Inuvik", "America/Winnipeg"} {
		loc, err := time.LoadLocation(z)
		if err != nil {
			fmt.Print(z, "=ERR(", err, ") ")
			continue
		}
		_, off := t.In(loc).Zone()
		fmt.Printf("%s=%+03d ", z, off/3600)
	}
	fmt.Println()
}
```

**pkg.** The release named by the image's tzdata package (`dpkg-query -W tzdata`, `rpm -q tzdata`, or the package status file in distroless images) and by the first line of `usr/share/zoneinfo/tzdata.zi`. For MySQL and MariaDB images we also loaded the image's zoneinfo into the server and checked `CONVERT_TZ` results.

**none.** `usr/share/zoneinfo` does not exist in the image.

**mongo.** `mongosh --quiet mongo.js` against a fresh `mongod` from the image, started without `--timeZoneInfo`, so it uses its built-in database.

```js
const z = [["America/Vancouver","2026-12-15T12:00:00Z"],["America/Edmonton","2026-12-15T12:00:00Z"],["America/Inuvik","2026-12-15T12:00:00Z"],["America/Winnipeg","2026-12-15T12:00:00Z"],["Africa/Casablanca","2026-10-13T12:00:00Z"]];
const p = {};
z.forEach(([n, t], i) => { p["z" + i] = {$dateToString: {date: new Date(t), format: "%z", timezone: n}}; });
p.wpgDayOf0530Z = {$dateToString: {date: new Date("2026-12-15T05:30:00Z"), format: "%Y-%m-%d", timezone: "America/Winnipeg"}};
const r = db.getSiblingDB("t").aggregate([{$documents: [{}]}, {$project: p}]).toArray()[0];
print(db.version(), z.map(([n], i) => n + "=" + r["z" + i]).join(" "), "wpgDayOf0530Z=" + r.wpgDayOf0530Z);
```

**es.** Elasticsearch and OpenSearch: the version in the bundled JDK's `jdk/lib/tzdb.dat`, printed by that JDK, plus a `date_histogram` with `calendar_interval: day` and `time_zone` set to each zone, on a document placed so that a stale copy moves it to the previous day.

**trino.** Queries against a stock `trinodb/trino:483` container. `hour()`, `timezone_hour()` and `format_datetime()` returned −7 for Vancouver (the Joda-Time copy, 2026b); `CAST(… AS varchar)` returned −8 (the JDK copy, 2026a).

```sql
SELECT hour(at_timezone(TIMESTAMP '2026-12-15 12:00:00 UTC', 'America/Vancouver'));
SELECT CAST(at_timezone(TIMESTAMP '2026-12-15 12:00:00 UTC', 'America/Vancouver') AS varchar);
```

**clickhouse.** `clickhouse-client --queries-file ch.sql` against the image's server.

```sql
SELECT version() AS v,
 timeZoneOffset(toDateTime('2026-12-15 12:00:00','America/Vancouver'))/3600 AS van,
 timeZoneOffset(toDateTime('2026-12-15 12:00:00','America/Edmonton'))/3600 AS edm,
 timeZoneOffset(toDateTime('2026-12-15 12:00:00','America/Inuvik'))/3600 AS inu,
 timeZoneOffset(toDateTime('2026-12-15 12:00:00','America/Winnipeg'))/3600 AS wpg,
 timeZoneOffset(toDateTime('2026-10-13 12:00:00','Africa/Casablanca'))/3600 AS cas,
 toDate(toDateTime64('2026-12-15 05:30:00',0,'UTC'),'America/Winnipeg') AS wpg_day_of_0530Z
FORMAT Vertical
```

**node.** Inside the image:

```sh
node -e 'const t=new Date("2026-12-15T12:00:00Z"); console.log(process.versions.tz, ...["America/Vancouver","America/Edmonton","America/Inuvik","America/Winnipeg","Africa/Casablanca"].map(z=>new Intl.DateTimeFormat("en",{timeZone:z,timeZoneName:"longOffset"}).formatToParts(t).find(p=>p.type=="timeZoneName").value))'
```

**python.** Inside the image, Python's `zoneinfo` (which reads the OS tree):

```sh
python3 -c 'import datetime as d, zoneinfo as z; t=d.datetime(2026,12,15,12,tzinfo=d.timezone.utc); print(*[t.astimezone(z.ZoneInfo(n)).utcoffset().total_seconds()/3600 for n in ["America/Vancouver","America/Edmonton","America/Inuvik","America/Winnipeg","Africa/Casablanca"]], z.TZPATH)'
```
