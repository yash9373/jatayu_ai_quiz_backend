import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db
from app.repositories.assessment_repo import AssessmentRepository
import json

async def test_paginated_assessments():
    """Test the get_assessments_by_test_id_paginated method"""
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Create repository instance
        repo = AssessmentRepository(db)
        
        print("🧪 Testing get_assessments_by_test_id_paginated for test_id=20")
        print("=" * 60)
        
        # Test 1: Basic pagination (page 1, 10 items)
        print("\n📄 Test 1: Basic pagination (page 1, 10 items)")
        result1 = await repo.get_assessments_by_test_id_paginated(
            test_id=20,
            skip=0,
            limit=10
        )
        
        print(f"✅ Total assessments: {result1['pagination']['total_count']}")
        print(f"✅ Current page: {result1['pagination']['current_page']}")
        print(f"✅ Total pages: {result1['pagination']['total_pages']}")
        print(f"✅ Items in this page: {len(result1['assessments'])}")
        
        if result1['assessments']:
            print(f"✅ First assessment: ID {result1['assessments'][0]['assessment_id']}, "
                  f"Candidate: {result1['assessments'][0]['candidate_name']}, "
                  f"Status: {result1['assessments'][0]['status']}")
        
        # Test 2: Filter by completed status
        print("\n📄 Test 2: Filter by 'completed' status")
        result2 = await repo.get_assessments_by_test_id_paginated(
            test_id=20,
            skip=0,
            limit=10,
            status_filter="completed"
        )
        
        print(f"✅ Completed assessments: {result2['pagination']['total_count']}")
        print(f"✅ Items in this page: {len(result2['assessments'])}")
        
        # Test 3: Filter by in_progress status
        print("\n📄 Test 3: Filter by 'in_progress' status")
        result3 = await repo.get_assessments_by_test_id_paginated(
            test_id=20,
            skip=0,
            limit=10,
            status_filter="in_progress"
        )
        
        print(f"✅ In-progress assessments: {result3['pagination']['total_count']}")
        print(f"✅ Items in this page: {len(result3['assessments'])}")
        
        # Test 4: Page 2 (if available)
        if result1['pagination']['total_pages'] > 1:
            print("\n📄 Test 4: Page 2")
            result4 = await repo.get_assessments_by_test_id_paginated(
                test_id=20,
                skip=10,
                limit=10
            )
            
            print(f"✅ Current page: {result4['pagination']['current_page']}")
            print(f"✅ Has previous: {result4['pagination']['has_previous']}")
            print(f"✅ Has next: {result4['pagination']['has_next']}")
            print(f"✅ Items in this page: {len(result4['assessments'])}")
        
        # Test 5: Small page size
        print("\n📄 Test 5: Small page size (3 items)")
        result5 = await repo.get_assessments_by_test_id_paginated(
            test_id=20,
            skip=0,
            limit=3
        )
        
        print(f"✅ Total pages with page_size=3: {result5['pagination']['total_pages']}")
        print(f"✅ Items in this page: {len(result5['assessments'])}")
        
        # Display sample assessment data
        if result1['assessments']:
            print("\n📊 Sample Assessment Data:")
            sample = result1['assessments'][0]
            print(f"   Assessment ID: {sample['assessment_id']}")
            print(f"   Candidate: {sample['candidate_name']} ({sample['candidate_email']})")
            print(f"   Status: {sample['status']}")
            print(f"   Score: {sample['percentage_score']}%")
            print(f"   Time taken: {sample['time_taken_display'] if 'time_taken_display' in sample else 'N/A'}")
            print(f"   Created: {sample['created_at']}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database session
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_paginated_assessments())
