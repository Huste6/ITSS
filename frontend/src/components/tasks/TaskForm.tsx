import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../../components/ui/form";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Button } from "../../components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Calendar } from "../../components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "../../components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import { cn } from "../../lib/utils";
import { getStudents } from "../../data/userData";
import axiosInstance from "../../axios-config";
const formSchema = z.object({
  title: z.string().min(3, "Task title must be at least 3 characters."),
  description: z
    .string()
    .min(10, "Description must be at least 10 characters."),
  status: z.string(),
  priority: z.string(),
  dueDate: z.date(),
  assigneeName: z.string().optional(),
});

type TaskFormValues = z.infer<typeof formSchema>;

interface TaskFormProps {
  initialData?: any;
  projectId: string;
  onSubmit: (data: TaskFormValues) => void;
  onCancel: () => void;
}

export function TaskForm({
  initialData,
  projectId,
  onSubmit,
  onCancel,
}: TaskFormProps) {
  const [loading, setLoading] = useState(false);
  const [students, setStudents] = useState<any[]>([]);

  // Parse dueDate from string to Date if it exists
  const initialDueDate = initialData?.dueDate
    ? new Date(initialData.dueDate)
    : new Date();

  const form = useForm<TaskFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: initialData?.title || "",
      description: initialData?.description || "",
      status: initialData?.status || "todo",
      priority: initialData?.priority || "medium",
      dueDate: initialDueDate,
      assigneeName: initialData?.assignee?.name || "",
    },
  });

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const studentData = await getStudents();
        // Filter students to only include those assigned to this project
        // Filter students to only include those assigned to this project
        // and exclude students with null groupId
        const filteredStudents = studentData.filter((student: any) => {
          return student.groupId && student.groupId._id === projectId;
        });

        console.log("Filtered Students:", filteredStudents);
        console.log("groupId:", projectId);
        console.log("All Students:", studentData);

        // Use the filtered students instead of all students
        setStudents(
          filteredStudents.map((student: any) => ({
            id: student.id,
            name: student.name,
          }))
        );
      } catch (error) {
        console.error("Error fetching students:", error);
      }
    };

    fetchStudents();
  }, []);

  const handleSubmit = async (data: TaskFormValues) => {
    try {
      setLoading(true);
      console.log("Form data:", data);
      console.log("Task create :", {
        title: data.title,
        description: data.description,
        group_id: projectId,
        assigned_student_id: [data.assigneeName],
        status: data.status,
        deadline: data.dueDate,
        priority: data.priority,
      });
      // await axiosInstance.post("/tasks/", {
      //   title: data.title,
      //   description: data.description,
      //   group_id: projectId,
      //   assigned_student_ids: [data.assigneeName],
      //   status: data.status,
      //   deadline: data.dueDate,
      //   priority: data.priority,
      // });

      // In a real app, we'd make an API call here
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulates API call
      onSubmit(data);
      toast.success(initialData ? "Task updatedeee" : "Task createdeeee");
    } catch (error) {
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Task Title</FormLabel>
              <FormControl>
                <Input
                  placeholder="Enter task title"
                  {...field}
                  className="border-academe-300 focus:ring-academe-400"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter task description"
                  className="resize-none min-h-[100px] border-academe-300 focus:ring-academe-400"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger className="border-academe-300 focus:ring-academe-400">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="todo">To Do</SelectItem>
                    <SelectItem value="in-progress">In Progress</SelectItem>
                    <SelectItem value="review">In Review</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="priority"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Priority</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger className="border-academe-300 focus:ring-academe-400">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="dueDate"
          render={({ field }) => (
            <FormItem className="flex flex-col">
              <FormLabel>Due Date</FormLabel>
              <Popover>
                <PopoverTrigger asChild>
                  <FormControl>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full pl-3 text-left font-normal border-academe-300 focus:ring-academe-400",
                        !field.value && "text-muted-foreground"
                      )}
                    >
                      {field.value ? (
                        format(field.value, "PPP")
                      ) : (
                        <span>Pick a date</span>
                      )}
                      <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                    </Button>
                  </FormControl>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={field.value}
                    onSelect={field.onChange}
                    disabled={(date: Date) =>
                      date < new Date(new Date().setHours(0, 0, 0, 0))
                    }
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="assigneeName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Assignee</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger className="border-academe-300 focus:ring-academe-400">
                    <SelectValue placeholder="Select a student" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {students.map((student) => (
                    <SelectItem key={student.id} value={student.id}>
                      {student.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
            className="border-academe-300 hover:bg-academe-50"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="bg-academe-500 hover:bg-academe-600"
          >
            {loading
              ? "Saving..."
              : initialData
              ? "Update Task"
              : "Create Task"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
