import axiosInstance from "../axios-config";
import { Project } from "../components/projects/ProjectCard";

let cachedProjects: Project[] = [];
let lastFetchTime: number = 0;
const CACHE_DURATION = 100 * 60 * 1000; // 5 phút cache

export const getProjects = async (forceRefresh = false): Promise<Project[]> => {
  const now = Date.now();

  // Nếu có cache và chưa hết hạn, và không yêu cầu refresh
  if (
    cachedProjects.length > 0 &&
    now - lastFetchTime < CACHE_DURATION &&
    !forceRefresh
  ) {
    return cachedProjects;
  }

  try {
    const response = await axiosInstance.get("/projects/");
    console.log("Projects fetched from API");

    cachedProjects = response.data.map((project: any) => ({
      id: project.id,
      title: project.title,
      description: project.description,
      mentorName: project.mentor.ho_ten,
      mentorId: project.mentor._id,
      status: "open",
      progress: 50,
      tags: project.tags,
    }));
    lastFetchTime = now;
    return cachedProjects;
  } catch (error) {
    console.error("Error fetching projects:", error);
    // Nếu có lỗi nhưng đã có cache trước đó, trả về cache cũ
    if (cachedProjects.length > 0) {
      console.warn("Using cached projects due to API error");
      return cachedProjects;
    }
    throw error;
  }
};

export const getCachedProjects = (): Project[] => {
  return cachedProjects;
};
