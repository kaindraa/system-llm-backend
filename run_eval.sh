#!/bin/bash
cd "c:\Users\pcgsa\Downloads\system-llm\system-llm-backend"
echo "Running SE Learning Evaluation..."
echo "======================================================================"
echo ""
echo "This will run:"
echo "  - Setup and imports"
echo "  - Database connection test"
echo "  - Multi-model evaluation (3 models x 5 test cases)"
echo ""
echo "======================================================================"
echo ""

# Run notebook with timeout of 30 minutes
timeout 1800 jupyter nbconvert \
  --to notebook \
  --execute se_learning_evaluation.ipynb \
  --output se_learning_evaluation_results.ipynb \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=python3

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "Evaluation completed successfully!"
    echo "Results saved to: se_learning_evaluation_results.ipynb"
    echo "======================================================================"
else
    echo ""
    echo "======================================================================"
    echo "Evaluation timed out or failed"
    echo "======================================================================"
fi
