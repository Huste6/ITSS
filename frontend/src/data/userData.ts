import axiosInstance from "../axios-config";
// import { Student, StudentMember } from "../components/groups/GroupCard";
import { Student } from "../types/group";
let cachedStudents: Student[] = [];
let lastFetchTime: number = 0;
const CACHE_DURATION = 100 * 60 * 1000; // 5 phút cache

export const getStudents = async (forceRefresh = false): Promise<Student[]> => {
  const now = Date.now();

  // Nếu có cache và chưa hết hạn, và không yêu cầu refresh
  if (
    cachedStudents.length > 0 &&
    now - lastFetchTime < CACHE_DURATION &&
    !forceRefresh
  ) {
    return cachedStudents;
  }

  try {
    console.log("Fetching students from API...");
    const response = await axiosInstance.get("/users/get-all");

    cachedStudents = response.data.map((student: any) => ({
      id: student.id,
      name: student.ho_ten,
      email: student.email,
      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
        student.ho_ten
      )}&background=random`,
      groupId: student.group_id,
    }));
    console.log("Cached students:", cachedStudents);
    lastFetchTime = now;
    return cachedStudents;
  } catch (error) {
    console.error("Error fetching students:", error);
    // Nếu có lỗi nhưng đã có cache trước đó, trả về cache cũ
    if (cachedStudents.length > 0) {
      console.warn("Using cached students due to API error");
      return cachedStudents;
    }
    throw error;
  }
};

export const getCachedStudents = (): Student[] => {
  return cachedStudents;
};
