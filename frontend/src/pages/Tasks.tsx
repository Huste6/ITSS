import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { TaskBoard } from "../components/tasks/TaskBoard";
import { Task, TaskCard } from "../components/tasks/TaskCard";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
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
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { useAuth } from "../contexts/AuthContext";
import { Plus } from "lucide-react";
import { toast } from "../components/ui/sonner";
import { Link } from "react-router-dom";
import { TaskForm } from "../components/tasks/TaskForm";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../axios-config";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "../components/ui/card";
import { getTasks } from "../data/taskData";
const Tasks = () => {
  const { user } = useAuth();
  console.log("User from context:", user);
  const [tasks, setTasks] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [projectFilter, setProjectFilter] = useState<string>("all");
  const recentTasks = tasks.slice(0, 20); // Example: Get the first 5 tasks as recent tasks
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);

  let projectId = "";
  if (user?.role === "student" && user?.groupId) {
    projectId = user?.groupId.id;
  } else {
    projectId = "kk";
  }
  // Mock data loading
  // useEffect(() => {
  //   const loadTasks = async () => {
  //     try {
  //       console.log("Loading Tasks...");

  //       const tasksData = await getTasks();

  //       const filteredTasks =
  //         user?.role === "student"
  //           ? tasksData.filter((task) => task.groupId === user.groupId.id)
  //           : tasksData;
  //       console.log("Filtered Tasks:", filteredTasks);
  //       setTasks(filteredTasks);
  //       console.log("Tasks state updated:", filteredTasks);
  //     } catch (error) {
  //       console.error("Error loading Tasks:", error);
  //       // Có thể thêm thông báo lỗi cho người dùng
  //     }
  //   };
  //   if (user?.id) {
  //     loadTasks();
  //   }
  // }, [user]);

  const handleTaskStatusChange = (
    taskId: string,
    newStatus: Task["status"]
  ) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId ? { ...task, status: newStatus } : task
      )
    );

    toast.success(`Task status updated to ${newStatus.replace("-", " ")}`);
  };

  const handleTaskClick = (task: Task) => {
    console.log("Task clicked:", task);
    // This would open a task detail dialog in a real application
  };

  // Unique projects for filter
  const projects = Array.from(
    new Set(
      tasks.map((task) => ({ id: task.projectId, title: task.projectTitle }))
    )
  );

  //   return (
  //     <DashboardLayout>
  //       <div className="space-y-6">
  //         <div className="flex justify-between items-center">
  //           <div>
  //             <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
  //             <p className="text-muted-foreground">
  //               {user?.role === "leader"
  //                 ? "Assign and manage tasks for your team members"
  //                 : "Track and update your assigned tasks"}
  //             </p>
  //           </div>

  //           {user?.role === "mentor" && (
  //             <Button>
  //               <Plus className="h-4 w-4 mr-2" /> Create Task
  //             </Button>
  //           )}
  //         </div>

  //         <div className="flex flex-col sm:flex-row gap-4">
  //           <div className="flex-1">
  //             <Input
  //               placeholder="Search tasks..."
  //               value={searchTerm}
  //               onChange={(e) => setSearchTerm(e.target.value)}
  //               className="w-full"
  //             />
  //           </div>
  //           <div className="w-full sm:w-48">
  //             <Select value={projectFilter} onValueChange={setProjectFilter}>
  //               <SelectTrigger>
  //                 <SelectValue placeholder="Filter by Project" />
  //               </SelectTrigger>
  //               <SelectContent>
  //                 <SelectItem value="all">All Projects</SelectItem>
  //                 {projects.map((project) => (
  //                   <SelectItem key={project.id} value={project.id}>
  //                     {project.title}
  //                   </SelectItem>
  //                 ))}
  //               </SelectContent>
  //             </Select>
  //           </div>
  //         </div>

  //         <TaskBoard
  //           tasks={tasks.filter(
  //             (task) =>
  //               (projectFilter === "all" || task.projectId === projectFilter) &&
  //               (task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
  //                 task.description
  //                   .toLowerCase()
  //                   .includes(searchTerm.toLowerCase()))
  //           )}
  //           onTaskClick={handleTaskClick}
  //           onTaskStatusChange={handleTaskStatusChange}
  //         />
  //       </div>
  //     </DashboardLayout>
  //   );
  // };
  const queryClient = useQueryClient();

  const handleCreateTask = async (formData: any) => {
    try {
      // Gọi API để tạo task mới
      const response = await axiosInstance.post("/tasks/", {
        title: formData.title,
        description: formData.description,
        group_id: projectId,
        assigned_student_ids: [formData.assigneeName],
        status: formData.status,
        deadline: formData.dueDate,
        priority: formData.priority,
      });

      const newTask = response.data;

      // Chuyển đổi `assigned_students` thành `assignee`
      const taskWithAssignee = {
        ...newTask,
        assignee: newTask.assigned_students.map((student: any) => ({
          id: student.id,
          name: student.name,
          avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
            student.name
          )}&background=random`,
        })),
        dueDate: newTask.deadline, // Đảm bảo `dueDate` được ánh xạ đúng
        projectId: newTask.group_id,
        projectTitle: newTask.group_name,
      };

      // Cập nhật danh sách task trong bộ nhớ cục bộ
      queryClient.setQueryData(["tasks"], (oldTasks: Task[] | undefined) => {
        return oldTasks ? [taskWithAssignee, ...oldTasks] : [taskWithAssignee];
      });

      toast.success("Task created successfully");
      setIsCreateOpen(false); // Đóng dialog tạo task
    } catch (error) {
      console.error("Failed to create task:", error);
      toast.error("Failed to create task. Please try again.");
    }
  };

  const fetchTasks = async () => {
    if (user?.groupId || user?.role === "mentor") {
      const response = await getTasks();
      // Filter tasks based on user role and group
      console.log("User role:", user?.groupId?.id);
      const filteredData =
        user?.role === "student"
          ? response.filter((task) => task.groupId === user.groupId?.id)
          : response;

      // For debugging
      console.log("Fetched tasks:", response);
      console.log("Filtered tasks:", filteredData);

      return filteredData;
    }
    return [];
  };

  const { data: fetchedTasks, isLoading: isFetchingTasks } = useQuery({
    queryKey: ["tasks"],
    queryFn: fetchTasks,
  });

  useEffect(() => {
    if (fetchedTasks) {
      setTasks(fetchedTasks);
    }
  }, [fetchedTasks]);

  if (isFetchingTasks) return <p>Loading tasks...</p>;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
            <p className="text-muted-foreground">
              {user?.role === "mentor"
                ? "Assign and manage tasks for your team members"
                : "Track and update your assigned tasks"}
            </p>
          </div>

          {user?.role === "student" && (
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create Task
            </Button>
          )}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogContent className="sm:max-w-[500px] border-academe-200">
              <DialogHeader>
                <DialogTitle className="text-academe-700">
                  Create New Task
                </DialogTitle>
              </DialogHeader>
              <TaskForm
                projectId={projectId}
                // projectTitle={projectTitle}
                onSubmit={handleCreateTask}
                onCancel={() => setIsCreateOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
        {/* Task Filters and Board */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="w-full sm:w-48">
            <Select value={projectFilter} onValueChange={setProjectFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by Project" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Recent Tasks */}
        <Card>
          {/* <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Recent Tasks</CardTitle>
                <CardDescription>
                  Your recently assigned or updated tasks
                </CardDescription>
              </div>
              <Button asChild>
                <Link to="/dashboard/tasks">View All</Link>
              </Button>
            </div>
          </CardHeader> */}
          <CardContent>
            {recentTasks.length === 0 ? (
              <p className="text-center py-8 text-muted-foreground">
                No tasks assigned yet
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recentTasks.map((task) => (
                  <TaskCard key={task.id} task={task} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* <TaskBoard
          tasks={tasks.filter(
            (task) =>
              (projectFilter === "all" || task.projectId === projectFilter) &&
              (task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                task.description
                  .toLowerCase()
                  .includes(searchTerm.toLowerCase()))
          )}
          onTaskClick={handleTaskClick}
          onTaskStatusChange={handleTaskStatusChange}
        /> */}
      </div>
    </DashboardLayout>
  );
};
export default Tasks;
