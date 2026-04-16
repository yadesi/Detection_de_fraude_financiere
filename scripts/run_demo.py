#!/usr/bin/env python3
"""
Complete Demo Runner for Fraud Detection System
Runs all demo scripts in sequence for comprehensive demonstration
"""

import subprocess
import time
import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoRunner:
    """Runs all demo scripts in sequence"""
    
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent
        
    def run_script(self, script_name: str, args: list = None) -> bool:
        """Run a single demo script"""
        
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
        
        try:
            logger.info(f"Running {script_name}...")
            
            # Build command
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)
            
            # Run script
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully completed {script_name}")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                logger.error(f"Script {script_name} failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out")
            return False
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
            return False
    
    def run_complete_demo(self):
        """Run complete demo sequence"""
        
        print("FRAUD DETECTION SYSTEM - COMPLETE DEMO")
        print("=" * 60)
        print("This demo will showcase all system features:")
        print("1. Data generation")
        print("2. Interactive API testing")
        print("3. Real-time alerts")
        print("4. Performance optimization")
        print("5. Production deployment")
        print("=" * 60)
        
        # Demo sequence
        demo_steps = [
            {
                "name": "Demo Data Generation",
                "script": "demo_data_generator.py",
                "description": "Generate realistic transaction data"
            },
            {
                "name": "Interactive API Demo",
                "script": "interactive_demo.py",
                "args": ["--demo", "all"],
                "description": "Test all API endpoints"
            },
            {
                "name": "Real-time Alerts",
                "script": "real_time_alerts.py",
                "description": "Demonstrate alert system"
            },
            {
                "name": "Performance Optimization",
                "script": "performance_optimizer.py",
                "description": "Show performance improvements"
            },
            {
                "name": "Production Deployment",
                "script": "production_deploy.py",
                "args": ["--dry-run"],
                "description": "Generate production manifests"
            }
        ]
        
        results = {}
        
        for i, step in enumerate(demo_steps, 1):
            print(f"\n{'='*60}")
            print(f"STEP {i}/{len(demo_steps)}: {step['name']}")
            print(f"{'='*60}")
            print(f"Description: {step['description']}")
            print()
            
            success = self.run_script(step['script'], step.get('args'))
            results[step['name']] = success
            
            if success:
                print(f"Step {i} completed successfully!")
            else:
                print(f"Step {i} failed!")
            
            # Pause between steps
            if i < len(demo_steps):
                print("\nPausing 3 seconds before next step...")
                time.sleep(3)
        
        # Summary
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")
        
        successful_steps = sum(1 for success in results.values() if success)
        total_steps = len(results)
        
        for step_name, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            print(f"  {step_name}: {status}")
        
        print(f"\nOverall: {successful_steps}/{total_steps} steps completed successfully")
        
        if successful_steps == total_steps:
            print("All demo steps completed successfully! System is ready for production.")
        else:
            print("Some demo steps failed. Please check the logs for details.")
        
        return successful_steps == total_steps
    
    def run_quick_demo(self):
        """Run quick demo for testing"""
        
        print("FRAUD DETECTION SYSTEM - QUICK DEMO")
        print("=" * 40)
        
        # Quick demo steps
        quick_steps = [
            {
                "name": "Data Generation",
                "script": "demo_data_generator.py"
            },
            {
                "name": "API Testing",
                "script": "interactive_demo.py",
                "args": ["--demo", "single"]
            }
        ]
        
        for step in quick_steps:
            print(f"\nRunning {step['name']}...")
            success = self.run_script(step['script'], step.get('args'))
            
            if not success:
                print(f"Failed at {step['name']}")
                return False
        
        print("\nQuick demo completed successfully!")
        return True

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Fraud Detection System Demo Runner")
    parser.add_argument("--mode", choices=["complete", "quick", "data", "api", "alerts", "performance", "deploy"], 
                       default="complete", help="Demo mode to run")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency checks")
    
    args = parser.parse_args()
    
    runner = DemoRunner()
    
    if args.mode == "complete":
        success = runner.run_complete_demo()
    elif args.mode == "quick":
        success = runner.run_quick_demo()
    elif args.mode == "data":
        success = runner.run_script("demo_data_generator.py")
    elif args.mode == "api":
        success = runner.run_script("interactive_demo.py", ["--demo", "all"])
    elif args.mode == "alerts":
        success = runner.run_script("real_time_alerts.py")
    elif args.mode == "performance":
        success = runner.run_script("performance_optimizer.py")
    elif args.mode == "deploy":
        success = runner.run_script("production_deploy.py", ["--dry-run"])
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
