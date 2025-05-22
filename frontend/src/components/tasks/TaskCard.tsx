import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Edit, Trash } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import { useEffect, useState } from "react";
import { Dialog } from "../ui/dialog";
import { TaskForm } from "./TaskForm";
import { DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
} from "../ui/alert-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import axios from "axios";
import axiosInstance from "../../axios-config";

export type Assignee = {
  id: string;
  name: string;
  avatar?: string;
};
export type Task = {
  id: string;
  title: string;
  description: string;
  groupId: string;
  status: "todo" | "in-progress" | "review" | "completed" | "pending";
  priority: "low" | "medium" | "high";
  dueDate: string;
  assignee?: any[];
  projectId: string;
  projectTitle: string;
};

type TaskCardProps = {
  task: Task;
  onClick?: () => void;
  compact?: boolean;
  actions?: React.ReactNode;
};

export function TaskCard({ task, onClick, compact = false }: TaskCardProps) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [deleteTaskId, setDeleteTaskId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const priorityColor = {
    low: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    medium:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };

  const statusColor = {
    todo: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
    "in-progress":
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    review:
      "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    completed:
      "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    pending:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  };

  const statusText = {
    todo: "To Do",
    "in-progress": "In Progress",
    review: "In Review",
    completed: "Completed",
    pending: "Pending",
  };

  const queryClient = useQueryClient();

  const deleteTaskMutation = useMutation({
    mutationFn: (taskId: string) => axiosInstance.delete(`/tasks/${taskId}`), // Gọi API xóa task
    onSuccess: (_, taskId) => {
      toast.success("Task deleted successfully");

      // Cập nhật danh sách task trong bộ nhớ cục bộ
      queryClient.setQueryData(["tasks"], (oldTasks: Task[] | undefined) => {
        return oldTasks ? oldTasks.filter((task) => task.id !== taskId) : [];
      });

      // Đóng dialog sau 1 giây
      setTimeout(() => {
        setIsDeleteDialogOpen(false); // Đóng dialog xác nhận xóa
        setIsDetailOpen(false); // Đóng dialog View Details
      }, 1000);
    },
    onError: () => {
      toast.error("Failed to delete task");
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: (updatedTask: Task) =>
      axiosInstance.put(`/tasks/${updatedTask.id}`, {
        title: updatedTask.title,
        description: updatedTask.description,
        group_id: updatedTask.projectId,
        assigned_student_ids: updatedTask.assignee?.map(
          (assignee) => assignee.id
        ),
        status: updatedTask.status,
        deadline: updatedTask.dueDate,
        priority: updatedTask.priority,
      }), // Gọi API sửa task
    onSuccess: (response) => {
      toast.success("Task updated successfully");

      // Chuyển đổi `assigned_students` thành `assignee`
      const updatedTask = {
        ...response.data,
        assignee: response.data.assigned_students.map(
          (student: { id: string; name: string }) => ({
            id: student.id,
            name: student.name,
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
              student.name
            )}&background=random`,
          })
        ),
      };

      // Cập nhật danh sách task trong bộ nhớ cục bộ
      queryClient.setQueryData(["tasks"], (oldTasks: Task[] | undefined) => {
        return oldTasks
          ? oldTasks.map((task) =>
              task.id === updatedTask.id ? updatedTask : task
            )
          : [];
      });

      setIsFormOpen(false); // Đóng form chỉnh sửa
    },
    onError: () => {
      toast.error("Failed to update task");
    },
  });

  useEffect(() => {
    if (deleteTaskId) {
      // Hiển thị xác nhận xóa hoặc gọi API xóa task
      // if (window.confirm("Are you sure you want to delete this task?")) {
      //   // console.log("Deleting task with ID:", deleteTaskId);
      //   // Gọi API xóa task tại đây
      //   setDeleteTaskId(null); // Reset state sau khi xóa
      // } else {
      //   setDeleteTaskId(null); // Hủy xóa
      // }
    }
  }, [deleteTaskId]);

  return (
    <Card
      className="card-hover border-l-4"
      style={{
        borderLeftColor:
          task.priority === "high"
            ? "#f87171"
            : task.priority === "medium"
            ? "#facc15"
            : "#4ade80",
      }}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-md">{task.title}</CardTitle>
          <Badge className={statusColor[task.status]} variant="outline">
            {statusText[task.status]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-2">
        {!compact && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {task.description}
          </p>
        )}
        <div className="flex justify-between items-center">
          <Badge className={priorityColor[task.priority]} variant="outline">
            {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}{" "}
            Priority
          </Badge>
          <span className="text-sm text-muted-foreground">
            Due: {new Date(task.dueDate).toLocaleDateString()}
          </span>
        </div>

        <div className="flex justify-between items-center mt-3">
          {task.assignee && task.assignee.length > 0 ? (
            <div className="flex items-center space-x-2">
              {task.assignee.map((assignee) => (
                <div key={assignee.id} className="flex items-center space-x-2">
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={assignee.avatar} />
                    <AvatarFallback>{assignee.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{assignee.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <span className="text-sm text-muted-foreground italic">
              Unassigned
            </span>
          )}
        </div>

        {!compact && (
          <div className="mt-3">
            <span className="text-xs text-muted-foreground">Group: </span>
            <span className="text-xs">{task.projectTitle}</span>
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-2 flex gap-2">
        {/* Nút chính (Start Task, Submit for Review, etc.) */}
        <Button
          onClick={() => setIsFormOpen(true)}
          className="flex-1"
          variant={task.status === "completed" ? "outline" : "default"}
        >
          {task.status === "todo"
            ? "Start Task"
            : task.status === "in-progress"
            ? "Submit for Review"
            : task.status === "review"
            ? "View Details"
            : "View Details"}
        </Button>

        {/* Nút View Details */}
        <Button
          onClick={() => setIsDetailOpen(true)}
          className="flex-1"
          variant="outline"
        >
          View Details
        </Button>

        {/* Dialog for Form */}
        {isFormOpen && (
          <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
            <DialogContent className="sm:max-w-[500px] border-academe-200">
              <DialogHeader>
                <DialogTitle>Edit Task</DialogTitle>
              </DialogHeader>
              <TaskForm
                initialData={task}
                projectId={task.projectId}
                onSubmit={(formData) => {
                  const updatedTask = {
                    ...task,
                    title: formData.title,
                    description: formData.description,
                    projectId: task.projectId,
                    assignee: formData.assigneeName
                      ? [
                          {
                            id: formData.assigneeName,
                            name: formData.assigneeName,
                          },
                        ]
                      : [],
                    status: formData.status as
                      | "todo"
                      | "in-progress"
                      | "review"
                      | "completed"
                      | "pending",
                    dueDate:
                      typeof formData.dueDate === "string"
                        ? formData.dueDate
                        : formData.dueDate.toISOString(),
                    priority: formData.priority as "low" | "medium" | "high",
                  };
                  updateTaskMutation.mutate(updatedTask); // Gọi mutation sửa task
                }}
                onCancel={() => setIsFormOpen(false)} // Đóng form khi hủy
              />
            </DialogContent>
          </Dialog>
        )}

        {/* Dialog for Task Details */}
        {isDetailOpen && (
          <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
            <DialogContent className="sm:max-w-[500px] border-academe-200">
              <DialogHeader>
                <DialogTitle className="text-academe-700">
                  Task Details
                </DialogTitle>
              </DialogHeader>
              {task && (
                <div className="space-y-4 mt-4">
                  <div>
                    <h3 className="font-medium text-sm text-muted-foreground">
                      Title
                    </h3>
                    <p>{task.title}</p>
                  </div>
                  <div>
                    <h3 className="font-medium text-sm text-muted-foreground">
                      Description
                    </h3>
                    <p>{task.description}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-medium text-sm text-muted-foreground">
                        Status
                      </h3>
                      <Badge
                        variant="outline"
                        className={
                          statusColor[task.status as keyof typeof statusColor]
                        }
                      >
                        {task.status === "in-progress"
                          ? "In Progress"
                          : task.status.charAt(0).toUpperCase() +
                            task.status.slice(1)}
                      </Badge>
                    </div>
                    <div>
                      <h3 className="font-medium text-sm text-muted-foreground">
                        Priority
                      </h3>
                      <Badge
                        variant="outline"
                        className={
                          priorityColor[
                            task.priority as keyof typeof priorityColor
                          ]
                        }
                      >
                        {task.priority.charAt(0).toUpperCase() +
                          task.priority.slice(1)}
                      </Badge>
                    </div>
                    <div>
                      <h3 className="font-medium text-sm text-muted-foreground">
                        Due Date
                      </h3>
                      <p>{new Date(task.dueDate).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <h3 className="font-medium text-sm text-muted-foreground">
                        Assignee
                      </h3>
                      <p>
                        {task.assignee && task.assignee.length > 0
                          ? task.assignee
                              .map((assignee) => assignee.name)
                              .join(", ")
                          : "Unassigned"}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 pt-4">
                    {/* Nút Edit */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setIsDetailOpen(false); // Đóng dialog chi tiết
                        setIsFormOpen(true); // Mở form chỉnh sửa
                      }}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>

                    {/* Nút Delete */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setIsDeleteDialogOpen(true); // Mở dialog xác nhận xóa
                      }}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>

                    {/* Nút Close */}
                    <Button
                      onClick={() => setIsDetailOpen(false)}
                      className="bg-academe-500 hover:bg-academe-600"
                    >
                      Close
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        )}

        <AlertDialog
          open={isDeleteDialogOpen}
          onOpenChange={setIsDeleteDialogOpen}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the
                task "{task.title}".
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDeleteDialogOpen(false)} // Đóng dialog khi hủy
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  console.log("Deleting task with ID:", task.id);
                  setIsDeleteDialogOpen(false); // Đóng dialog sau khi xóa
                  setDeleteTaskId(task.id); // Gọi logic xóa task
                  deleteTaskMutation.mutate(task.id); // Gọi mutation xóa task
                }}
              >
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  );
}
