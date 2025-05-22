import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { Button } from "../components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Project } from "../components/projects/ProjectCard";
// import { TaskList } from "../components/tasks/TaskList";
// import { GroupList } from "../components/groups/GroupList";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";
import { ArrowLeft, Edit, Trash } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import { ProjectForm } from "../components/projects/ProjectForm";
import axiosInstance from "../axios-config";
import { Task } from "../components/tasks/TaskCard";
import { getTasks } from "../data/taskData";
import { getGroups } from "../data/groupData";
import { TaskList } from "../components/tasks/TaskList";
import { GroupList } from "../components/groups/GroupList";
import { Group } from "../components/groups/GroupCard";
import { title } from "process";
// Mock project data
const mockProject: Project = {
  id: "project1",
  title: "Research on Machine Learning Applications",
  description:
    "A comprehensive study of machine learning applications in healthcare",
  mentorName: "Dr. Smith",
  mentorId: "mentor1",
  status: "in-progress",
  progress: 35,
  tags: ["Machine Learning", "Healthcare", "Research"],
};

// Mock tasks data
const mockTasks = [
  {
    id: "task1",
    title: "Literature Review",
    description:
      "Review existing research papers on the topic and create a summary",
    status: "in-progress",
    priority: "high",
    dueDate: "2025-05-20",
    assignee: {
      id: "user1",
      name: "John Doe",
    },
    projectId: "project1",
    projectTitle: "Research on Machine Learning Applications",
  },
  {
    id: "task2",
    title: "Data Collection",
    description: "Collect dataset from the provided sources",
    status: "todo",
    priority: "medium",
    dueDate: "2025-05-25",
    assignee: {
      id: "user1",
      name: "John Doe",
    },
    projectId: "project1",
    projectTitle: "Research on Machine Learning Applications",
  },
];

// Mock groups data
const mockGroups = [
  {
    id: "group1",
    name: "ML Analysis Team",
    description: "Focused on analyzing machine learning algorithms",
    leaderId: "leader1",
    leaderName: "Jane Leader",
    members: 3,
    projectId: "project1",
    projectTitle: "Research on Machine Learning Applications",
  },
  {
    id: "group2",
    name: "Data Collection Team",
    description: "Responsible for gathering and preprocessing data",
    leaderId: "leader2",
    leaderName: "Mike Stewart",
    members: 2,
    projectId: "project1",
    projectTitle: "Research on Machine Learning Applications",
  },
];

const ProjectDetail = () => {
  const { projectId } = useParams<{ projectId: string }>();
  // console.log("Project ID:", id);
  const navigate = useNavigate();
  const { user } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  // const [groups, setGroups] = useState<Group[]>([]);

  // Fetch project data
  useEffect(() => {
    const fetchProjectData = async () => {
      setIsLoading(true);
      try {
        // In a real app, this would be an API call
        const response = await axiosInstance.get(`/projects/${projectId}`);
        const newProject = {
          id: response.data._id,
          title: response.data.title,
          description: response.data.description,
          mentorName: response.data.mentor.ho_ten,
          mentorId: response.data.mentor._id,
          status: response.data.status,
          progress: response.data.progress,
          tags: response.data.tags,
        };
        console.log("Project data fetched:", newProject);
        await new Promise((resolve) => setTimeout(resolve, 800));
        setProject(newProject);
        // setTasks(mockTasks);
        // setGroups(mockGroups);
      } catch (error) {
        toast.error("Failed to load project details");
      } finally {
        setIsLoading(false);
      }
    };
    const loadTasks = async () => {
      try {
        const taskData = await getTasks();
        setTasks(taskData);
        console.log("Tasks state updated:", taskData);
      } catch (error) {
        console.error("Error loading tasks:", error);
        // Có thể thêm thông báo lỗi cho người dùng
      }
    };
    const loadGroups = async () => {
      try {
        console.log("Loading projects...");
        const projectsData = await getGroups();
        const formattedGroups = projectsData.map((group: any) => ({
          id: group.id,
          name: group.name,
          leader: group.leader,
          leaderId: group.leaderId,
          description: group.description || "",
          projectId: group.projectId,
          projectTitle: group.projectTitle,
          members: group.members.map((member: any) => ({
            id: member.id,
            name: member.name,
          })),
          progress: group.progress || 0,
          hasUnreadMessages: group.hasUnreadMessages || false,
        }));
        const filteredGroups = projectsData.filter(
          (group: any) => group.projectId === projectId
        );
        console.log("gr data fetched:", projectsData);
        setGroups(filteredGroups);
        console.log("Groupstate updated:", formattedGroups);
      } catch (error) {
        console.error("Error loading projects:", error);
        // Có thể thêm thông báo lỗi cho người dùng
      }
    };
    fetchProjectData();
    loadTasks();
    loadGroups();
  }, [projectId]);

  const handleDelete = async () => {
    try {
      await axiosInstance.delete(`/projects/${projectId}`);
      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast.success("Project deleted successfully");
      window.location.href = `/dashboard/projects`;
    } catch (error) {
      toast.error("Failed to delete project");
    }
  };

  interface UpdateProjectData {
    title: string;
    description: string;
    tags: string[];
  }

  const handleUpdateProject = async (data: UpdateProjectData) => {
    // In a real app, this would update the project via API
    console.log("Updating project with data:", data);
    await axiosInstance.put(`/projects/${projectId}`, {
      title: data.title,
      description: data.description,
      tags: data.tags,
    });
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setProject({
      ...project!,
      title: data.title,
      description: data.description,
    });
    setIsEditing(false);
    toast.success("Project updated successfully");
  };

  // Filter groups based on user role
  const visibleGroups =
    user?.role === "student"
      ? groups.filter((group) =>
          group.members.some((member) => member.id === user.id)
        )
      : groups;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-pulse text-lg">
            Loading project details...
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-96">
          <h2 className="text-xl font-semibold">Project not found</h2>
          <p className="text-muted-foreground mb-4">
            The project you're looking for doesn't exist or has been removed.
          </p>
          <Button onClick={() => navigate("/dashboard/projects")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  // const canEdit = user?.role === "mentor" && user?.id === project.mentorId;
  const canEdit = user?.role === "mentor" || user?.role === "admin";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {isEditing ? (
          <div className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">Edit Project</h2>
            <ProjectForm
              initialData={project}
              onSubmit={handleUpdateProject}
              onCancel={() => setIsEditing(false)}
            />
          </div>
        ) : (
          <>
            <div className="flex justify-between items-start">
              <div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/dashboard/projects")}
                  className="mb-4"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Projects
                </Button>
                <h1 className="text-3xl font-bold">{project.title}</h1>
                <p className="text-muted-foreground mt-2">
                  {project.description}
                </p>
              </div>

              {canEdit && (
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setDeleteDialogOpen(true)}
                  >
                    <Trash className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-muted/30 p-4 rounded-lg">
                <h3 className="font-medium text-sm text-muted-foreground">
                  Mentor
                </h3>
                <p className="font-medium">{project.mentorName}</p>
              </div>

              {/* <div className="bg-muted/30 p-4 rounded-lg">
                <h3 className="font-medium text-sm text-muted-foreground">
                  Team Leader
                </h3>
                <p className="font-medium">
                  {project.teamLeaderName || "Not assigned"}
                </p>
              </div> */}

              <div className="bg-muted/30 p-4 rounded-lg">
                <h3 className="font-medium text-sm text-muted-foreground">
                  Status
                </h3>
                <p className="font-medium capitalize">
                  {project.status === "in-progress"
                    ? "In Progress"
                    : project.status}
                </p>
              </div>

              {/* <div className="bg-muted/30 p-4 rounded-lg">
                <h3 className="font-medium text-sm text-muted-foreground">
                  Progress
                </h3>
                <p className="font-medium">{project.progress}%</p>
              </div> */}
            </div>
          </>
        )}

        {!isEditing && (
          <Tabs defaultValue="groups" className="w-full mt-6">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              {/* <TabsTrigger value="tasks">Tasks</TabsTrigger> */}
              <TabsTrigger value="groups">Groups</TabsTrigger>
            </TabsList>
            {/* <TabsContent value="tasks">
              <div className="bg-card p-6 rounded-lg border">
                <TaskList tasks={tasks} projectId={project.id} />
              </div>
            </TabsContent> */}
            <TabsContent value="groups">
              <div className="bg-card p-6 rounded-lg border">
                {visibleGroups.length > 0 ? (
                  <GroupList groups={visibleGroups} projectId={project.id} />
                ) : (
                  <p>No groups available</p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              project and all associated tasks and groups.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  );
};

export default ProjectDetail;
