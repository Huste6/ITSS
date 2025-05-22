from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Any
from models.group_model import Group
from models.project_model import Project
from models.user_model import User
from models.task_model import Task
from schemas.group_schemas import GroupCreate, GroupResponse, PyObjectId
from routes.user_routes import get_current_mentor
from routes.user_routes import get_current_user
from beanie import Link
import asyncio
import logging
from bson import ObjectId

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    responses={404: {"description": "Not found"}},
)
@router.post("/add-github-link/{group_id}", response_model=dict,
             description="Add a GitHub link to a group. Only the mentor who created the project can add a GitHub link.",
             summary="Add GitHub link to group")
async def add_github_link(group_id: str, github_link: str, current_user: User = Depends(get_current_user)):
    try:
        # Validate the group_id format
        logger.info(f"Group ID: {group_id}")
        group_id_obj = PyObjectId.validate(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id format")
    
    try:
        # Fetch the group from the database
        group = await Group.get(group_id_obj)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        group.github_link = github_link
        await group.save()

        logger.info(f"Added GitHub link to group {group.id}")

        return {
            "group_id": str(group.id),
            "github_link": group.github_link
        }
    except Exception as e:
        logger.error(f"Error adding GitHub link to group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
@router.post("/", response_model=GroupResponse,
             description="Create a new group. Only the mentor who created the project can create groups.",
             summary="Create a new group")
async def create_group(group: GroupCreate, current_user: User = Depends(get_current_mentor)):
    try:
        group.project_id = PyObjectId.validate(group.project_id)
        project = await Project.get(group.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Fetch mentor từ project để kiểm tra
        # mentor = await project.mentor.fetch()
        if not current_user:
            logger.error(f"Mentor not found for project {project.id}")
            raise HTTPException(status_code=404, detail="Mentor associated with project not found")

        if str(current_user.id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Lấy leader từ leader_id
        leader_id_obj = PyObjectId.validate(group.leader_id)
        leader = await User.get(leader_id_obj)
        if not leader:
            raise HTTPException(status_code=404, detail="Leader not found")
        if leader.role != "student":
            raise HTTPException(status_code=400, detail="Leader must be a student")
        if leader.group_id:
            raise HTTPException(status_code=400, detail="Leader is already in another group")

        members = []
        member = await User.get(PyObjectId(group.leader_id))
        members.append(Link(member, document_class=User))

        new_group = Group(
            name=group.name,
            project=Link(project, document_class=Project),
            leaders=Link(leader, document_class=User),
            members=members,
            tasks=[],
            allTasks=[]
        )
                
        await new_group.insert()
        
        db_project = await Project.get(group.project_id)
        db_project.groups.append(Link(new_group, document_class=Group))
        await db_project.save()

        # Update the group_id for the leader and members
        db_leader = await User.get(leader_id_obj)
        db_leader.group_id = Link(new_group, document_class=Group)
        await db_leader.save()

        logger.info(f"Created new group: {new_group.id}")

        member_data = []
        for member_link in new_group.members:
            member = await member_link.fetch() if isinstance(member_link, Link) else member_link
            member_data.append({
                "id": str(member.id),
                "ho_ten": member.ho_ten,
                "email": member.email
            })

        return GroupResponse(
            id=str(new_group.id),
            name=new_group.name,
            project_id=str(project.id),
            project_title=project.title,
            project_description=project.description,
            leader_id=str(leader.id),
            leader_email=leader.email,
            leader_name=leader.ho_ten,
            member_ids=[member["id"] for member in member_data],
            member_names=[member["ho_ten"] for member in member_data],
            member_emails=[member["email"] for member in member_data]
        )

    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
@router.get("/{group_id}",
             response_model=dict,
             description="Get detailed information about a specific group by ID. Only the mentor who created the project can view the group.",
             summary="Get group by ID")
async def get_group_by_group_id(group_id: str, current_user: User = Depends(get_current_user)):
    try:
        # Validate the group_id format
        logger.info(f"Group ID: {group_id}")
        group_id_obj = PyObjectId.validate(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id format")
    
    try:
        logger.info(f"Group ID Object: {group_id_obj}")
        # Fetch the group from the database
        group = await Group.get(group_id_obj)
        logger.info(f"Group found: {group}")
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Fetch project to check mentor and get project details
        project = await group.project.fetch() if isinstance(group.project, Link) else group.project
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if the current user is the mentor of the project
        # mentor = await project.mentor.fetch() if isinstance(project.mentor, Link) else project.mentor
        # if not mentor or str(mentor.id) != str(current_user.id):
        #     raise HTTPException(status_code=403, detail="Not authorized")

        # Fetch leader
        leader = await group.leaders.fetch() if isinstance(group.leaders, Link) else group.leaders
        if not leader:
            logger.warning(f"Failed to fetch leader for group {group.id}")
            raise HTTPException(status_code=404, detail="Leader not found")

        # Fetch members
        member_data = []
        for member_link in group.members:
            member = await member_link.fetch() if isinstance(member_link, Link) else member_link
            if member:
                member_data.append({
                    "id": str(member.id),
                    "ho_ten": member.ho_ten,
                    "email": member.email
                })

        # Prepare response
        # return GroupResponse(
        #     id=str(group.id),
        #     name=group.name,
        #     project_id=str(project.id),
        #     project_title=project.title,
        #     project_description=project.description,
        #     leader_id=str(leader.id),
        #     leader_name=leader.ho_ten,
        #     leader_email=leader.email,
        #     member_ids=[member["id"] for member in member_data],
        #     member_names=[member["ho_ten"] for member in member_data],
        #     member_emails=[member["email"] for member in member_data]
        # )
        return {
            "id": str(group.id),
            "name": group.name,
            "project_id": str(project.id),
            "project_title": project.title,
            "project_description": project.description,
            "leader_id": str(leader.id),
            "leader_name": leader.ho_ten,
            "leader_email": leader.email,
            "member_ids": [member["id"] for member in member_data],
            "member_names": [member["ho_ten"] for member in member_data],
            "member_emails": [member["email"] for member in member_data],
            "github_link": group.github_link
        }
    except Exception as e:
        logger.error(f"Error fetching group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/", response_model=List[dict],
            description="Get all groups. Only the mentor who created the project can view its groups cai dcm.",
            summary="Get all groups") 
async def get_all_groups(current_user: User = Depends(get_current_user),
                         skip: int = Query(0, ge=0, description="Number of groups to skip"),
                         limit: int = Query(50, ge=1, le=100, description="Maximum number of groups to return")):
    try:
        # Fetch all groups from the database
        groups = await Group.find().skip(skip).limit(limit).to_list()
        result = []
        for group in groups:
            mentor = await group.leaders.fetch() if isinstance(group.leaders, Link) else group.leaders
            if not mentor or str(mentor.id) != str(current_user.id):
                pass
                # continue  # Skip groups not associated with the current mentor
            # Fetch project and leader and members
            project = await group.project.fetch() if isinstance(group.project, Link) else group.project
            leader = await group.leaders.fetch() if isinstance(group.leaders, Link) else group.leaders
            members = []
            for member_link in group.members:
                member = await member_link.fetch() if isinstance(member_link, Link) else member_link
                members.append({
                    "id": str(member.id),
                    "ho_ten": member.ho_ten,
                    "email": member.email
                })
            result.append({
                "id": str(group.id),
                "name": group.name,
                "project_id": str(project.id),
                "project_title": project.title,
                "project_description": project.description,
                "leader_id": str(leader.id),
                "leader_name": leader.ho_ten,
                "leader_email": leader.email,
                "members": members,
                "github_link" : group.github_link
            })

        return result
    except Exception as e:
        logger.error(f"Error fetching all groups: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{group_id}/add-member/{member_id}", response_model=bool,
             description="Add a member to a group. Only the mentor who created the project can add members.",
             summary="Add a member to a group")
async def add_member_to_group(group_id: str, member_id: str, current_user: User = Depends(get_current_mentor)):

    try:
        # Validate group_id and member_id
        group_id_obj = PyObjectId.validate(group_id)
        member_id_obj = PyObjectId.validate(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id or member_id format")

    try:
        # Fetch the group from the database
        group = await Group.get(group_id_obj)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")


        member = await User.get(member_id_obj)
        print(f"Member: {member}")
        print(member.group_id, "dcmm")
        if member.group_id:
            raise HTTPException(status_code=400, detail="Member is already in another group")
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Check if the member is already in the group
        if member in group.members:
            raise HTTPException(status_code=400, detail="Member is already in the group")

        # Add the member to the group
        # member.group_id = group_id
        # print(f"Member group_id: {member.group_id}")
        # await member.save()
        db_leader = await User.get(member_id_obj)
        db_leader.group_id = Link(group, document_class=Group)
        await db_leader.save()
        group.members.append(Link(member, document_class=User))
        await group.save()

        logger.info(f"Added member {member.id} to group {group.id}")
        return True
    except Exception as e:
        logger.error(f"Error adding member {member_id} to group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{group_id}/change-leader/{new_leader_id}", response_model=dict,
             description="Change the leader of a group. Only the mentor who created the project can change the leader.",
             summary="Change group leader")
async def change_group_leader(group_id: str, new_leader_id: str, current_user: User = Depends(get_current_mentor)):
    """
    Change the leader of a group.
    """
    try:
        # Validate group_id and new_leader_id
        group_id_obj = PyObjectId.validate(group_id)
        new_leader_id_obj = PyObjectId.validate(new_leader_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id or new_leader_id format")

    try:
        # Fetch the group from the database
        group = await Group.get(group_id_obj)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        members = []
        for member_link in group.members:
            member = await member_link.fetch() if isinstance(member_link, Link) else member_link
            members.append(member)
        # Fetch the new leader from the database
        new_leader = await User.get(new_leader_id_obj)
        print(f"New leader: {new_leader}")
        if not new_leader:
            raise HTTPException(status_code=404, detail="New leader not found")

        # Ensure the new leader is a student
        if new_leader.role != "student":
            raise HTTPException(status_code=400, detail="New leader must be a student")

        # Ensure the new leader is a member of the group
        member_ids = [member.id for member in members]
        if new_leader_id_obj not in member_ids:
            raise HTTPException(status_code=400, detail="New leader is not a member of the group")
        # Update the leader of the group
        group.leaders = Link(new_leader, document_class=User)
        await group.save()

        logger.info(f"Changed leader of group {group.id} to {new_leader.id}")
        # Prepare the response
        return {
            "message": "Leader changed successfully",
            "new_leader_id": str(new_leader.id),
            "new_leader_name": new_leader.ho_ten,
            "group_name": group.name,
            "group_id": str(group.id)
        }
    except Exception as e:
        logger.error(f"Error changing leader of group {group_id} to {new_leader_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# @router.delete("/{group_id}/remove-member/{member_id}", response_model=dict)
# async def remove_member_from_group(group_id: str, member_id: str, current_user: User = Depends(get_current_mentor)):
#     """
#     Remove a member from a group.
#     """
#     try:
#         # Validate group_id and member_id
#         group_id_obj = PyObjectId.validate(group_id)
#         member_id_obj = PyObjectId.validate(member_id)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid group_id or member_id format")

#     try:
#         # Fetch the group from the database
#         group = await Group.get(group_id_obj)
#         if not group:
#             raise HTTPException(status_code=404, detail="Group not found")

#         # Fetch the member from the database
#         member = await User.get(member_id_obj)
#         if not member:
#             raise HTTPException(status_code=404, detail="Member not found")

#         members = await asyncio.gather(*[member.fetch() for member in group.members])
#         # Ensure the member is part of the group
#         if member_id_obj not in [m.id for m in members]:
#             raise HTTPException(status_code=400, detail="Member is not part of the group")

#         # Remove the member from the group
#         group.members = [m for m in members if m.id != member_id_obj]
#         await group.save()

#         # Update the member's group_id to None
#         member.group_id = None
#         await member.save()

#         logger.info(f"Removed member {member.id} from group {group.id}")

#         # Prepare the response
#         return {
#             "message": "Member removed successfully",
#             "removed_member_id": str(member.id),
#             "group_name": group.name,
#             "group_id": str(group.id)
#         }
#     except Exception as e:
#         logger.error(f"Error removing member {member_id} from group {group_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
@router.delete("/{group_id}/remove-member/{member_id}", response_model=dict)
async def remove_member_from_group(group_id: str, member_id: str, current_user: User = Depends(get_current_mentor)):
    """
    Remove a member from a group.
    """
    try:
        # Validate group_id and member_id
        group_id_obj = PyObjectId.validate(group_id)
        member_id_obj = PyObjectId.validate(member_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id or member_id format")

    try:
        # Fetch the group from the database
        group = await Group.get(group_id_obj)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Fetch the member from the database
        member = await User.get(member_id_obj)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Fetch all members to compare IDs
        fetched_members = []
        for member_link in group.members:
            fetched_member = await member_link.fetch() if isinstance(member_link, Link) else member_link
            fetched_members.append(fetched_member)

        # Check if the member is in the group by comparing IDs
        if not any(fetched_member.id == member_id_obj for fetched_member in fetched_members):
            raise HTTPException(status_code=400, detail="Member is not in the group")

        # Remove the member by filtering the original Link list
        group.members = [
            member_link for member_link in group.members
            if (await member_link.fetch() if isinstance(member_link, Link) else member_link).id != member_id_obj
        ]
        await group.save()

        # Update the member's group_id to None
        member.group_id = None
        await member.save()
        logger.info(f"Removed member {member.id} from group {group.id}")

        # Prepare the response
        return {
            "message": "Member removed successfully",
            "removed_member_id": str(member.id),
            "group_name": group.name,
            "group_id": str(group.id)
        }
    except Exception as e:
        logger.error(f"Error removing member {member_id} from group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{group_id}")
async def delete_group(group_id: str, current_user: User = Depends(get_current_mentor)):
    try:
        group_id_obj = PyObjectId.validate(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group_id format")

    try:
        group = await Group.get(group_id_obj)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")


        # Delete all tasks in the group
        tasks = await group.fetch_link("allTasks") or []
        for task in tasks:
            await task.delete()

        # Remove group reference from members
        members = []
        for member_link in group.members:
            member = await member_link.fetch() if isinstance(member_link, Link) else member_link
            members.append(member)
        for member in members:
            member.group_id = None
            await member.save()  # Removed fetch_links=False

        # Delete the group
        await group.delete()

        logger.info(f"Deleted group: {group_id}")

        return {"message": "Group deleted"}
    except Exception as e:
        logger.error(f"Error deleting group: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")