FROM maven:3.9-eclipse-temurin-11 AS builder
WORKDIR /app
COPY wvanalyzer/pom.xml ./wvanalyzer/pom.xml
RUN mvn -f /app/wvanalyzer/pom.xml -B dependency:go-offline
COPY wvanalyzer/src ./wvanalyzer/src
RUN mvn -f /app/wvanalyzer/pom.xml -B clean package -DskipTests

# ---------------------------------------

FROM eclipse-temurin:11-jre
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends parallel && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wvanalyzer/target/wvmc.analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar /app/analyzer.jar
COPY docker_entrypoint.sh /app/docker_entrypoint.sh
RUN chmod +x /app/docker_entrypoint.sh

ENTRYPOINT ["/app/docker_entrypoint.sh", "/app/analyzer.jar"]
