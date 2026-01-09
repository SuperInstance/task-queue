// Simple example demonstrating task-queue usage in Go
//
// Run this example after starting a worker:
// go run main.go

package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/task-queue/go/taskqueue"
)

// Task handlers
func add(ctx context.Context, x, y int) (interface{}, error) {
	log.Printf("Adding %d + %d", x, y)
	return x + y, nil
}

func processData(ctx context.Context, data []int) (interface{}, error) {
	log.Printf("Processing %d items", len(data))
	sum := 0
	for _, v := range data {
		sum += v
	}
	time.Sleep(1 * time.Second)
	return map[string]interface{}{
		"processed": len(data),
		"sum":       sum,
	}, nil
}

func urgentTask(ctx context.Context, message string) (interface{}, error) {
	log.Printf("URGENT: %s", message)
	return message, nil
}

func flakyTask(ctx context.Context, attempt int) (interface{}, error) {
	log.Printf("Attempt %d", attempt)
	if attempt < 3 {
		return nil, fmt.Errorf("not ready yet!")
	}
	return "Success!", nil
}

func main() {
	// Create queue
	queue := taskqueue.NewQueue(
		"default",
		"redis://localhost:6379/0",
	)

	fmt.Println("Enqueuing tasks...")

	// Simple task
	task1, err := queue.Enqueue("add", 5, 3)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Task 1 ID: %s\n", task1.ID)

	// Task with complex arguments
	data := make([]int, 100)
	for i := range data {
		data[i] = i
	}
	task2, err := queue.Enqueue("processData", data)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Task 2 ID: %s\n", task2.ID)

	// Urgent task
	task3, err := queue.Enqueue(
		"urgentTask",
		"Process this immediately!",
		taskqueue.WithQueue("high_priority"),
		taskqueue.WithPriority(0),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Task 3 ID: %s\n", task3.ID)

	// Flaky task (will retry)
	task4, err := queue.Enqueue(
		"flakyTask",
		1,
		taskqueue.WithRetries(3),
		taskqueue.WithRetryBackoff(true),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Task 4 ID: %s\n", task4.ID)

	fmt.Println("\nWaiting for results...")

	// Get results with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result1, err := task1.Get(ctx)
	if err != nil {
		log.Printf("Task 1 failed: %v", err)
	} else {
		fmt.Printf("Result 1: %v\n", result1)
	}

	result2, err := task2.Get(ctx)
	if err != nil {
		log.Printf("Task 2 failed: %v", err)
	} else {
		fmt.Printf("Result 2: %v\n", result2)
	}

	result3, err := task3.Get(ctx)
	if err != nil {
		log.Printf("Task 3 failed: %v", err)
	} else {
		fmt.Printf("Result 3: %v\n", result3)
	}

	ctx4, cancel4 := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel4()
	result4, err := task4.Get(ctx4)
	if err != nil {
		log.Printf("Task 4 failed: %v", err)
	} else {
		fmt.Printf("Result 4: %v\n", result4)
	}

	fmt.Println("\nAll tasks completed!")
}
