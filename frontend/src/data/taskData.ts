import axiosInstance from "../axios-config";
import { Task } from "../components/tasks/TaskCard";
let cachedTasks: Task[] = [];
let lastFetchTime: number = 0;
const CACHE_DURATION = 100 * 60 * 1000;

export const getTasks = async (forceRefresh = false): Promise<Task[]> => {
  const now = Date.now();

  // If cache exists, is not expired, and no refresh is requested
  if (
    cachedTasks.length > 0 &&
    now - lastFetchTime < CACHE_DURATION &&
    !forceRefresh
  ) {
    return cachedTasks;
  }
  try {
    console.log("Fetching tasks from API...");
    const response = await axiosInstance.get("/tasks/");
    console.log("Tasks fetched from API", response.data);
    cachedTasks = response.data.map((task: any) => ({
      id: task.id,
      title: task.title,
      description: task.description,
      status: task.status,
      groupId: task.group_id,
      priority: "medium",
      dueDate: task.deadline,
      assignee: task.assigned_students.map((student: any) => ({
        id: student._id,
        name: student.ho_ten || "dcm",
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
          student.ho_ten
        )}&background=random`,
      })),
      projectId: task.group_id,
      projectTitle: task.group_name,
    }));
    console.log("Cached tasks:", cachedTasks);
    lastFetchTime = now;
    return cachedTasks;
  } catch (error) {
    console.error("Error fetching tasks:", error);
    // If there's an error but cache exists, return the old cache
    if (cachedTasks.length > 0) {
      console.warn("Using cached tasks due to API error");
      return cachedTasks;
    }
    throw error;
  }
};

export const getCachedTasks = (): Task[] => {
  return cachedTasks;
};
