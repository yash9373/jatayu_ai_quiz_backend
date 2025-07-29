import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db
from app.repositories.assessment_repo import AssessmentRepository
from app.controllers.assessment_controller import get_assessments_by_test_id
from fastapi import Request
import json

async def test_controller_endpoint():
    """Test the actual controller endpoint with pagination"""
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        print("🎯 Testing Controller Endpoint with Pagination")
        print("=" * 60)
        
        # Import the controller function (we'll simulate the FastAPI request)
        from app.controllers.assessment_controller import get_assessments_by_test_id
        
        # Test with default pagination
        print("\n📄 Test 1: Default pagination (page=1, page_size=10)")
        result = await get_assessments_by_test_id(
            test_id=20,
            db=db,
            page=1,
            page_size=10,
            status=None
        )
        
        print(f"✅ Test ID: {result['test_id']}")
        print(f"✅ Total assessments: {result['total_assessments']}")
        print(f"✅ Current page: {result['pagination']['current_page']}")
        print(f"✅ Total pages: {result['pagination']['total_pages']}")
        print(f"✅ Page size: {result['pagination']['page_size']}")
        print(f"✅ Has next: {result['pagination']['has_next']}")
        print(f"✅ Has previous: {result['pagination']['has_previous']}")
        
        # Display assessment details
        if result['assessments']:
            assessment = result['assessments'][0]
            print(f"\n📊 Assessment Details:")
            print(f"   Assessment ID: {assessment['assessment_id']}")
            print(f"   Candidate: {assessment['candidate_name']}")
            print(f"   Email: {assessment['candidate_email']}")
            print(f"   Status: {assessment['status']}")
            print(f"   Score: {assessment['score_display']}")
            print(f"   Time taken: {assessment['time_taken_display']}")
            print(f"   Start time: {assessment['start_time']}")
            print(f"   End time: {assessment['end_time']}")
            print(f"   Created: {assessment['created_at']}")
        
        # Test pagination with smaller page size
        print("\n📄 Test 2: Small page size (page_size=1)")
        result2 = await get_assessments_by_test_id(
            test_id=20,
            db=db,
            page=1,
            page_size=1,
            status=None
        )
        
        print(f"✅ Total pages with page_size=1: {result2['pagination']['total_pages']}")
        print(f"✅ Items in current page: {len(result2['assessments'])}")
        
        # Test status filtering
        print("\n📄 Test 3: Filter by 'completed' status")
        result3 = await get_assessments_by_test_id(
            test_id=20,
            db=db,
            page=1,
            page_size=10,
            status="completed"
        )
        
        print(f"✅ Completed assessments: {result3['pagination']['total_count']}")
        print(f"✅ Filter applied: {result3['filters']['status']}")
        
        # Test summary statistics
        print(f"\n📊 Summary Statistics:")
        summary = result['summary']
        print(f"   Completed on page: {summary['page_completed']}")
        print(f"   In progress on page: {summary['page_in_progress']}")
        print(f"   Average score on page: {summary['page_average_score']}")
        print(f"   Page size: {summary['page_size']}")
        
        print("\n🎉 All controller tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_controller_endpoint())
