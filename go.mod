module github.com/task-queue/go

go 1.21

require (
	github.com/redis/go-redis/v9 v9.3.0
	github.com/streadway/amqp v1.1.0
	github.com/google/uuid v1.3.1
	github.com/codingbrain/clipper v0.2.0
	gopkg.in/yaml.v3 v3.0.1
)

require (
	github.com/cespare/xxhash/v2 v2.2.0 // indirect
	github.com/dgryski/go-rendezvous v0.0.0-20200823014737-9f7001d12a5f // indirect
)

// Development dependencies
// dev: github.com/stretchr/testify v1.8.4
// dev: github.com/golangci/golangci-lint v1.52.0
