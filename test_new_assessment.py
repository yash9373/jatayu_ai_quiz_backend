"""
Test creating a new assessment with timezone-aware datetime handling
"""
import asyncio
from datetime import datetime, timezone
from app.db.database import get_db
from app.repositories.assessment_repo import AssessmentRepository


async def test_new_assessment_creation():
    """Test creating a new assessment to verify timezone handling"""
    print("Testing new assessment creation with timezone awareness...")

    async for db in get_db():
        try:
            repo = AssessmentRepository(db)

            # Test data - you may need to adjust these IDs based on your actual data
            test_application_id = 1  # Adjust as needed
            test_user_id = 2  # Adjust as needed
            test_test_id = 20  # Using test_id 20 as we've been testing with it

            print(f"Attempting to create assessment for:")
            print(f"  Application ID: {test_application_id}")
            print(f"  User ID: {test_user_id}")
            print(f"  Test ID: {test_test_id}")
            print(
                f"  Current UTC time: {datetime.now(timezone.utc).isoformat()}")

            # Check if assessment already exists for this user and test
            existing = await repo.get_user_assessment_for_test(test_user_id, test_test_id)
            if existing:
                print(
                    f"Assessment already exists with ID: {existing.assessment_id}")
                print(f"  Status: {existing.status}")
                print(f"  Created at: {existing.created_at}")
                print(
                    f"  Timezone info: {existing.created_at.tzinfo if existing.created_at else 'None'}")
                return

            # Create new assessment
            assessment_id = await repo.create_assessment_instance(
                application_id=test_application_id,
                user_id=test_user_id,
                test_id=test_test_id
            )

            if assessment_id:
                print(
                    f"\n✅ Successfully created assessment with ID: {assessment_id}")

                # Fetch the created assessment to verify timezone handling
                created_assessment = await repo.get_assessment_by_id(assessment_id)
                if created_assessment:
                    print(f"\n=== Created Assessment Details ===")
                    print(f"Assessment ID: {created_assessment.assessment_id}")
                    print(f"Status: {created_assessment.status}")
                    print(f"Created at: {created_assessment.created_at}")
                    print(f"  Type: {type(created_assessment.created_at)}")
                    print(
                        f"  Timezone: {created_assessment.created_at.tzinfo}")
                    print(
                        f"  ISO format: {created_assessment.created_at.isoformat()}")
                    print(f"Updated at: {created_assessment.updated_at}")
                    print(f"  Type: {type(created_assessment.updated_at)}")
                    print(
                        f"  Timezone: {created_assessment.updated_at.tzinfo}")
                    print(
                        f"  ISO format: {created_assessment.updated_at.isoformat()}")

                    # Test updating the assessment
                    print(f"\n=== Testing Assessment Update ===")
                    # Small delay to see time difference
                    await asyncio.sleep(1)

                    success = await repo.update_assessment_status(
                        assessment_id=assessment_id,
                        status="completed",
                        percentage_score=85.5,
                        end_time=datetime.now(timezone.utc)
                    )

                    if success:
                        print("✅ Successfully updated assessment")

                        # Fetch updated assessment
                        updated_assessment = await repo.get_assessment_by_id(assessment_id)
                        if updated_assessment:
                            print(
                                f"Updated status: {updated_assessment.status}")
                            print(
                                f"Updated score: {updated_assessment.percentage_score}")
                            print(
                                f"Updated at: {updated_assessment.updated_at}")
                            print(
                                f"  Timezone: {updated_assessment.updated_at.tzinfo}")
                            print(f"End time: {updated_assessment.end_time}")
                            print(
                                f"  Timezone: {updated_assessment.end_time.tzinfo if updated_assessment.end_time else 'None'}")
                    else:
                        print("❌ Failed to update assessment")
                else:
                    print("❌ Could not fetch created assessment")
            else:
                print("❌ Failed to create assessment")

        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_new_assessment_creation())
