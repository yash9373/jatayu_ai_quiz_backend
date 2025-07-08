#!/bin/bash
# Remove all assessment and candidate files except candidate_application
rm -f app/models/assessment.py
rm -f app/models/candidate.py
rm -f app/repositories/assessment_repo.py
rm -f app/repositories/candidate_repo.py
rm -f app/schemas/assessment_schema.py
rm -f app/schemas/candidate_schema.py
rm -f app/services/assessment_service.py
rm -f app/services/candidate_service.py
rm -f app/controllers/assessment_controller.py
rm -f app/controllers/candidate_controller.py
