# PowerShell script to remove all assessment and candidate files except candidate_application
Remove-Item app/models/assessment.py -ErrorAction SilentlyContinue
Remove-Item app/models/candidate.py -ErrorAction SilentlyContinue
Remove-Item app/repositories/assessment_repo.py -ErrorAction SilentlyContinue
Remove-Item app/repositories/candidate_repo.py -ErrorAction SilentlyContinue
Remove-Item app/schemas/assessment_schema.py -ErrorAction SilentlyContinue
Remove-Item app/schemas/candidate_schema.py -ErrorAction SilentlyContinue
Remove-Item app/services/assessment_service.py -ErrorAction SilentlyContinue
Remove-Item app/services/candidate_service.py -ErrorAction SilentlyContinue
Remove-Item app/controllers/assessment_controller.py -ErrorAction SilentlyContinue
Remove-Item app/controllers/candidate_controller.py -ErrorAction SilentlyContinue
