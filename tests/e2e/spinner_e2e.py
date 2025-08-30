"""
End-to-end tests for spinner utility

Tests complete user workflows and visual output scenarios.
"""

import time
import subprocess
import pytest
from src.utils.spinner import show_spinner, Spinner


class TestSpinnerE2E:
    """End-to-end tests for spinner in complete workflows."""
    
    def test_spinner_with_real_file_operation(self, tmp_path):
        """Test spinner during actual file operations."""
        test_file = tmp_path / "test_data.txt"
        
        with show_spinner("morphing", "Creating test file"):
            # Simulate file creation with some processing time
            test_file.write_text("Test data" * 1000)
            time.sleep(0.1)  # Simulate processing delay
        
        assert test_file.exists()
        assert len(test_file.read_text()) > 0
    
    def test_spinner_with_network_simulation(self):
        """Test spinner during simulated network operation."""
        result = None
        
        with show_spinner("claude", "Fetching data"):
            # Simulate network delay
            time.sleep(0.2)
            result = {"status": "success", "data": "fetched"}
        
        assert result is not None
        assert result["status"] == "success"
    
    def test_spinner_in_cli_workflow(self):
        """Test spinner as part of complete CLI workflow."""
        operations = [
            ("brightness", "Initializing", 0.1),
            ("pulse", "Processing", 0.15),
            ("morphing", "Finalizing", 0.1)
        ]
        
        results = []
        for spinner_type, operation, duration in operations:
            with show_spinner(spinner_type, operation):
                time.sleep(duration)
                results.append(f"{operation} complete")
        
        assert len(results) == 3
        assert all("complete" in result for result in results)
    
    def test_spinner_error_recovery_workflow(self):
        """Test spinner in error scenarios with recovery."""
        try:
            with show_spinner("pulse", "Risky operation"):
                time.sleep(0.1)
                raise ConnectionError("Network failed")
        except ConnectionError:
            pass  # Expected error
        
        # Should be able to continue with new spinner
        with show_spinner("morphing", "Recovery operation"):
            time.sleep(0.1)
            # Recovery successful
    
    def test_spinner_with_data_processing_pipeline(self):
        """Test spinner in complete data processing pipeline."""
        data = list(range(100))
        processed_data = []
        
        # Stage 1: Data validation
        with show_spinner("brightness", "Validating data"):
            time.sleep(0.08)
            validated = [x for x in data if x >= 0]
        
        # Stage 2: Data transformation  
        with show_spinner("claude", "Transforming data"):
            time.sleep(0.12)
            transformed = [x * 2 for x in validated]
        
        # Stage 3: Data aggregation
        with show_spinner("morphing", "Aggregating results"):
            time.sleep(0.1)
            processed_data = sum(transformed)
        
        assert processed_data > 0
        assert processed_data == sum(x * 2 for x in range(100))
    
    @pytest.mark.slow
    def test_spinner_long_operation_workflow(self):
        """Test spinner during genuinely long operation."""
        with show_spinner("pulse", "Long computation"):
            # Simulate CPU intensive task
            total = 0
            for i in range(10000):
                total += i ** 2
            time.sleep(0.5)  # Additional delay
        
        assert total > 0
    
    def test_multiple_sequential_operations(self):
        """Test complete workflow with multiple sequential operations."""
        workflow_steps = [
            ("Setup", "brightness", 0.08),
            ("Authentication", "claude", 0.12),
            ("Data retrieval", "morphing", 0.1),
            ("Processing", "pulse", 0.15),
            ("Cleanup", "brightness", 0.05)
        ]
        
        completed_steps = []
        
        for step_name, spinner_type, duration in workflow_steps:
            with show_spinner(spinner_type, step_name):
                time.sleep(duration)
                completed_steps.append(step_name)
        
        assert len(completed_steps) == len(workflow_steps)
        assert completed_steps == [step[0] for step in workflow_steps]
    
    def test_spinner_with_user_interaction_simulation(self):
        """Test spinner in scenarios that simulate user interaction."""
        user_choices = ["option1", "option2", "option3"]
        selected_choice = None
        
        # Simulate user making choice while system processes
        with show_spinner("morphing", "Preparing options"):
            time.sleep(0.1)
            # Simulate user selection
            selected_choice = user_choices[1]
        
        # Process user choice
        with show_spinner("claude", f"Processing {selected_choice}"):
            time.sleep(0.12)
            result = f"Processed {selected_choice}"
        
        assert selected_choice == "option2"
        assert "option2" in result
    
    def test_spinner_performance_under_load(self):
        """Test spinner performance with multiple concurrent operations."""
        import threading
        
        results = []
        
        def worker(worker_id):
            with show_spinner("pulse", f"Worker {worker_id}"):
                # Simulate work
                time.sleep(0.15)
                results.append(f"Worker {worker_id} done")
        
        # Create multiple workers
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=2.0)
        
        assert len(results) == 3
        assert all("done" in result for result in results)