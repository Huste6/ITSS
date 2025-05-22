// import { useState, useEffect } from "react";
// import { DashboardLayout } from "../components/layout/DashboardLayout";
// import { ProjectList } from "../components/projects/ProjectList";
// import { Project } from "../components/projects/ProjectCard";
// import { Button } from "../components/ui/button";
// import { useAuth } from "../contexts/AuthContext";
// import { Plus } from "lucide-react";
// import axiosInstance from "../axios-config";
// const Projects = () => {
//   const { user } = useAuth();
//   const [projects, setProjects] = useState<Project[]>([]);

//   // Mock data loading
//   useEffect(() => {
//     // Generate mock project data
//     const fetchProjects = async () => {
//       try {
//         const response = await axiosInstance.get("/projects");
//         console.log("Projects fetched:", response.data);
//         // Giả sử API trả về mảng projects
//         const projectsData = response.data.map((project: any) => ({
//           id: project._id,
//           title: project.title,
//           description: project.description,
//           mentorName: project.mentor.ho_ten,
//           mentorId: project.mentor._id,
//           teamLeaderId: "con cac",
//           teamLeaderName: "dau buoi",
//           members: 4,
//           status: "open",
//           progress: 50,
//           tags: ["tag1", "tag2"],
//         }));
//         setProjects(projectsData);
//         console.log("Projects state updated:", projectsData);
//       } catch (error) {
//         console.error("Error fetching projects:", error);
//         // Có thể thêm thông báo lỗi cho người dùng
//       }
//     };
//     fetchProjects();
//   }, [user]);

//   const handleProjectClick = (project: Project) => {
//     alert(`Project clicked: ${project.title}`);
//     console.log("Project clicked:", project);
//     // This would navigate to project details in a real application
//   };

//   return (
//     <DashboardLayout>
//       <div className="space-y-6">
//         <div className="flex justify-between items-center">
//           <div>
//             <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
//             <p className="text-muted-foreground">
//               {user?.role === "mentor"
//                 ? "Create and manage academic projects"
//                 : user?.role === "leader"
//                 ? "Lead and organize your project teams"
//                 : "Browse and join academic projects"}
//             </p>
//           </div>

//           {user?.role === "mentor" && (
//             <Button>
//               <Plus className="h-4 w-4 mr-2" /> Create Project
//             </Button>
//           )}
//         </div>

//         <ProjectList projects={projects} onProjectClick={handleProjectClick} />
//       </div>
//     </DashboardLayout>
//   );
// };

// export default Projects;
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { ProjectList } from "../components/projects/ProjectList";
import { Project } from "../components/projects/ProjectCard";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { Plus } from "lucide-react";
import { getProjects } from "../data/projectsData";
import { toast } from "sonner";
import { ProjectForm } from "../components/projects/ProjectForm";
import axiosInstance from "../axios-config";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
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
const Projects = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const projectsData = await getProjects();
        setProjects(projectsData);
        console.log("Projects state updated:", projectsData);
      } catch (error) {
        console.error("Error loading projects:", error);
        // Có thể thêm thông báo lỗi cho người dùng
      }
    };

    if (user?.id) {
      loadProjects();
    }
  }, [user]);

  const handleProjectClick = (project: Project) => {
    navigate(`/dashboard/projects/${project.id}`);
  };
  const handleCreateProject = async (projectData: any) => {
    // Create new project object
    const newProject: Project = {
      id: `project${projects.length + 1}`,
      title: projectData.title,
      description: projectData.description,
      mentorName: user?.role === "mentor" ? user.name : projectData.mentorName,
      mentorId:
        user?.role === "mentor" ? user.id : `mentor${projects.length + 1}`,
      status: "open",
      progress: 0,
      tags: projectData.tags || [],
    };
    const postPrj = {
      title: newProject.title,
      description: newProject.description,
      tags: newProject.tags,
    };
    const response = await axiosInstance.post("/projects/", postPrj);
    console.log("response", response.data);
    newProject.id = response.data.id;
    console.log("newprj", newProject);
    setProjects([...projects, newProject]);
    setIsCreateDialogOpen(false);
    toast.success("Project created successfully");
  };
  const handleEditProject = (projectData: any) => {
    if (!selectedProject) return;

    // Update the project
    const updatedProjects = projects.map((project) =>
      project.id === selectedProject.id
        ? {
            ...project,
            title: projectData.title,
            description: projectData.description,
            teamLeaderName: projectData.teamLeaderName,
            // teamLeaderId: projectData.teamLeaderId || project.teamLeaderId,
            tags: projectData.tags || project.tags,
          }
        : project
    );

    setProjects(updatedProjects);
    setIsEditDialogOpen(false);
    setSelectedProject(null);
    toast.success("Project updated successfully");
  };
  const handleDeleteProject = () => {
    if (!selectedProject) return;

    // Remove the project
    const filteredProjects = projects.filter(
      (project) => project.id !== selectedProject.id
    );
    setProjects(filteredProjects);
    setIsDeleteDialogOpen(false);
    setSelectedProject(null);
    toast.success("Project deleted successfully");
  };

  const handleEditClick = (project: Project) => {
    setSelectedProject(project);
    setIsEditDialogOpen(true);
  };

  const handleDeleteClick = (project: Project) => {
    setSelectedProject(project);
    setIsDeleteDialogOpen(true);
  };

  return (
    <DashboardLayout>
      {/* Giữ nguyên phần JSX */}
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground">
              {user?.role === "mentor"
                ? "Create and manage academic projects"
                : user?.role === "leader"
                ? "Lead and organize your project teams"
                : "Browse and join academic projects"}
            </p>
          </div>

          {user?.role === "mentor" && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create Project
            </Button>
          )}
        </div>

        <ProjectList
          projects={projects}
          onProjectClick={handleProjectClick}
          onEditClick={handleEditClick}
          onDeleteClick={handleDeleteClick}
          userRole={user?.role || "student"}
          userId={user?.id || ""}
        />
      </div>
      {/* Create Project Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
          </DialogHeader>
          <ProjectForm
            onSubmit={handleCreateProject}
            onCancel={() => setIsCreateDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
      {/* Edit Project Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
          </DialogHeader>
          {selectedProject && (
            <ProjectForm
              initialData={selectedProject}
              onSubmit={handleEditProject}
              onCancel={() => setIsEditDialogOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
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
              onClick={handleDeleteProject}
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

export default Projects;
