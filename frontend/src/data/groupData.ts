import { green } from "@mui/material/colors";
import axiosInstance from "../axios-config";
import { Group, GroupMember } from "../components/groups/GroupCard";
let cachedGroups: Group[] = [];
let lastFetchTime: number = 0;
const CACHE_DURATION = 100 * 60 * 1000; // 5 phút cache

export const getGroups = async (forceRefresh = false): Promise<Group[]> => {
  const now = Date.now();

  // Nếu có cache và chưa hết hạn, và không yêu cầu refresh
  if (
    cachedGroups.length > 0 &&
    now - lastFetchTime < CACHE_DURATION &&
    !forceRefresh
  ) {
    return cachedGroups;
  }

  try {
    console.log("Fetching groups from API...");
    const response = await axiosInstance.get("/groups/");
    console.log("Groups fetched from API", response.data);
    cachedGroups = response.data.map((group: any) => ({
      id: group.id,
      name: group.name,
      leader: group.leader_name,
      leaderId: group.leader_id,
      projectId: group.project_id,
      projectTitle: group.project_title,
      members: group.members.map((member: any) => ({
        id: member.id,
        name: member.ho_ten,
        email: member.email,
        role: member.id === group.leader_id ? "leader" : "member",
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
          member.ho_ten
        )}&background=random`,
      })),
      progress: 50,
      hasUnreadMessages: true,
      githubLink: group.github_link,
    }));
    console.log("Cached groups:", cachedGroups);
    lastFetchTime = now;
    return cachedGroups;
  } catch (error) {
    console.error("Error fetching groups:", error);
    // Nếu có lỗi nhưng đã có cache trước đó, trả về cache cũ
    if (cachedGroups.length > 0) {
      console.warn("Using cached groups due to API error");
      return cachedGroups;
    }
    throw error;
  }
};
export const getGroupById = async (
  groupId: string
): Promise<Group | undefined> => {
  const cachedGroup = cachedGroups.find((group) => group.id === groupId);
  if (cachedGroup) {
    return cachedGroup;
  }

  // Nếu không tìm thấy trong cache, gọi API để lấy dữ liệu nhóm
  try {
    console.log(`Fetching group with ID ${groupId} from API...`);
    const response = await axiosInstance.get(`/groups/${groupId}`);
    const group = {
      id: response.data.id,
      name: response.data.name,
      leader: response.data.leader_name,
      projectId: response.data.project_id,
      projectTitle: response.data.project_title,
      members: response.data.members.map((member: any) => ({
        id: member.id,
        name: member.ho_ten,
        email: member.email,
        role: member.ho_ten === response.data.leader_name ? "leader" : "member",
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(
          member.ho_ten
        )}&background=random`,
      })),
      progress: 50,
      githubLink: response.data.github_link,
      hasUnreadMessages: true,
    };

    // Cập nhật cachedGroups
    cachedGroups.push(group);
    return group;
  } catch (error) {
    console.error(`Error fetching group with ID ${groupId}:`, error);
    throw error;
  }
};

export const getCachedGroups = (): Group[] => {
  return cachedGroups;
};
