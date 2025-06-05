import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { Button } from "../components/ui/button";
import { useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { TaskList } from "../components/tasks/TaskList";
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
import { toast } from "sonner";
import { ArrowLeft, Trash, UserPlus, Users } from "lucide-react";
import { GroupDetailHeader } from "../components/groups/GroupDetailHeader";
import { GroupMemberList } from "../components/groups/GroupMemberList";
import { AddMemberDialog } from "../components/groups/AddMemberDialog";
import { ChangeLeaderDialog } from "../components/groups/ChangeLeaderDialog";
import {
  getGroupById,
  deleteGroup,
  addGroupMember,
  removeGroupMember,
  changeGroupLeader,
} from "../services/groupService";
import { getGroupById as getGR } from "../data/groupData";
import { GroupMember } from "../types/group";
import { Skeleton } from "../components/ui/skeleton";
import { useAuth } from "../contexts/AuthContext";
import { getTasks } from "../data/taskData";
import { Task } from "../components/tasks/TaskCard";
import axiosInstance from "../axios-config";
import GroupEvaluationTab from "../components/groups/GroupEvaluationTab";

const getFreeRiders = async (groupId: string) => {
  try {
    // Lấy tất cả members của group
    const group = await getGR(groupId);
    if (!group || !group.members || group.members.length === 0) return [];

    // Lấy tất cả evaluations của các thành viên
    const evaluationsRes = await axiosInstance.get(
      `/evaluations?group_id=${groupId}`
    );
    const evaluations = evaluationsRes.data || [];

    // Tính điểm trung bình evaluation cho từng member
    const memberScores: Record<string, number> = {};
    group.members.forEach((member: any) => {
      const memberEvals = evaluations.filter(
        (e: any) => e.student?.id === member.id
      );
      if (memberEvals.length > 0) {
        memberScores[member.id] =
          memberEvals.reduce((sum: number, e: any) => sum + (e.score || 0), 0) /
          memberEvals.length;
      } else {
        memberScores[member.id] = 0;
      }
    });

    // Tìm điểm thấp nhất
    const minScore = Math.min(...Object.values(memberScores));
    // Lấy tất cả member có điểm thấp nhất
    const freeRiders = group.members.filter(
      (m: any) => memberScores[m.id] === minScore
    );

    // Thêm dữ liệu fix cứng cho mỗi free rider
    const fixedData = [
      {
        score: 2.5,
        commit_count: 3,
        lines_added: 10,
        lines_removed: 5,
        files_modified: 1,
        last_commit_date: "2025-06-01T10:00:00Z",
      },
      {
        score: 2.5,
        commit_count: 2,
        lines_added: 5,
        lines_removed: 2,
        files_modified: 1,
        last_commit_date: "2025-06-02T12:00:00Z",
      },
    ];

    // Gán dữ liệu fix cứng vào từng free rider (nếu có nhiều hơn 2 thì lặp lại dữ liệu fix cứng)
    return freeRiders.map((member: any, idx: number) => ({
      ...member,
      ...fixedData[idx % fixedData.length],
    }));
  } catch (error) {
    console.error("Error fetching free riders by evaluation:", error);
    return [];
  }
};

// Hàm mới: getFreeRidersFromAPI với timeout 10s
const getFreeRidersFromAPI = async (groupId: string) => {
  return new Promise<any[]>((resolve, reject) => {
    let didTimeout = false;
    const timeout = setTimeout(() => {
      didTimeout = true;
      reject(new Error("Limit exceed: No data after 10 seconds"));
    }, 10000);

    axiosInstance
      .get(`/free_rider/get_free_rider?group_id=${groupId}`)
      .then((res) => {
        if (!didTimeout) {
          clearTimeout(timeout);
          resolve(res.data || []);
        }
      })
      .catch((err) => {
        if (!didTimeout) {
          clearTimeout(timeout);
          reject(err);
        }
      });
  });
};

const getGitHubCommits = async (username: string, repoName: string) => {
  try {
    // const response = await fetch(
    //   `http://localhost:8000/github/repos?username=${username}&repo_name=ITSS&type=commits`
    // );
    const response = await axiosInstance.get(
      `/github/repos?username=${username}&repo_name=${repoName}&type=commits`
    );

    if (!response) {
      throw new Error("Failed to fetch GitHub commits");
    }
    return await response.data;
  } catch (error) {
    console.error("Error fetching GitHub commits:", error);
    return [];
  }
};
const GroupDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isMentor = user?.role === "mentor";
  const [commits, setCommits] = useState<any[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isAddMemberDialogOpen, setIsAddMemberDialogOpen] = useState(false);
  const [isChangeLeaderDialogOpen, setIsChangeLeaderDialogOpen] =
    useState(false);
  const [isAddGitHubDialogOpen, setIsAddGitHubDialogOpen] = useState(false);
  const [githubLinkInput, setGitHubLinkInput] = useState("");
  const [freeRiders, setFreeRiders] = useState<any[]>([]);
  const [isLoadingFreeRider, setIsLoadingFreeRider] = useState(false);
  const projectId = id;

  // Lấy tasks bằng react-query
  const { data: allTasks = [], isLoading: isLoadingTasks } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => getTasks(),
    refetchOnWindowFocus: true,
    staleTime: 0,
  });
  const taskss = allTasks.filter((task) => task.projectId === id);

  const {
    data: group,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["group", id],
    queryFn: () => getGR(id!),
    enabled: !!id,
    refetchOnWindowFocus: true,
    staleTime: 0, // luôn lấy mới khi invalidate
  });

  // window.location.reload();
  console.log("groupss", group);

  const deleteGroupMutation = useMutation({
    mutationFn: () => deleteGroup(id!),
    onSuccess: () => {
      toast.success("Group deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      navigate("/dashboard/groups");
    },
    onError: () => {
      toast.error("Failed to delete group");
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: (member: Omit<GroupMember, "role">) =>
      addGroupMember(id!, member),
    onSuccess: () => {
      toast.success("Member added successfully");
      queryClient.invalidateQueries({ queryKey: ["group", id] });
      setIsAddMemberDialogOpen(false);
      refetch(); // <-- Thêm dòng này để lấy lại dữ liệu group mới nhất
    },
    onError: () => {
      toast.error("Failed to add member");
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (memberId: string) => removeGroupMember(id!, memberId),
    onSuccess: () => {
      toast.success("Member removed successfully");
      queryClient.invalidateQueries({ queryKey: ["group", id] });
    },
    onError: () => {
      toast.error("Failed to remove member");
    },
  });

  const changeLeaderMutation = useMutation({
    mutationFn: (newLeaderId: string) => changeGroupLeader(id!, newLeaderId),
    onSuccess: () => {
      toast.success("Group leader changed successfully");
      queryClient.invalidateQueries({ queryKey: ["group", id] });
      setIsChangeLeaderDialogOpen(false);
    },
    onError: () => {
      toast.error("Failed to change group leader");
    },
  });

  const updateGitHubLinkMutation = useMutation({
    mutationFn: (newGitHubLink: string) =>
      axiosInstance.post(
        `/groups/add-github-link/${id}?github_link=${encodeURIComponent(
          newGitHubLink
        )}`
      ),
    onSuccess: () => {
      toast.success("GitHub link updated successfully");

      // Cập nhật cục bộ GitHub link
      queryClient.setQueryData(["group", id], (oldGroup: any) => ({
        ...oldGroup,
        githubLink: githubLinkInput.trim(),
      }));

      setIsAddGitHubDialogOpen(false);
    },
    onError: () => {
      toast.error("Failed to update GitHub link");
    },
  });

  const fetchFreeRiders = async () => {
    if (!id) return;
    setIsLoadingFreeRider(true);
    try {
      const data = await getFreeRidersFromAPI(id);
      setFreeRiders(data);
    } catch (e: any) {
      if (e.message && e.message.includes("Limit exceed")) {
        toast.error("Limit exceed: Không có dữ liệu sau 10 giây.");
      } else {
        toast.error("Failed to fetch free riders");
      }
      setFreeRiders([]);
    }
    setIsLoadingFreeRider(false);
  };

  // useEffect(() => {
  //   if (group?.githubLink) {
  //     const fetchCommits = async () => {
  //       try {
  //         const githubUrl = new URL(group.githubLink as string);
  //         const pathParts = githubUrl.pathname.split("/").filter(Boolean);
  //         if (pathParts.length < 2) {
  //           console.error("Invalid GitHub link format.");
  //           return;
  //         }

  //         const username = pathParts[0];
  //         const repoName = pathParts[1];

  //         const commitData = await getGitHubCommits(username);
  //         setCommits(commitData);
  //         console.log("Commits state updated:", commitData);
  //       } catch (error) {
  //         console.error("Error fetching GitHub commits:", error);
  //       }
  //     };

  //     fetchCommits();
  //   }
  // }, [group?.githubLink]);

  // Tính progress dựa trên taskss
  const completedTasks = taskss.filter((t) => t.status === "completed").length;
  const totalTasks = taskss.length;
  const progress =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Skeleton className="h-8 w-[250px]" />
              <Skeleton className="h-4 w-[350px]" />
            </div>
            <Skeleton className="h-10 w-[100px]" />
          </div>

          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-[150px]" />
              <Skeleton className="h-4 w-[250px]" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[300px] w-full" />
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (!group) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-[70vh]">
          <h1 className="text-2xl font-bold mb-4">Group Not Found</h1>
          <p className="text-muted-foreground mb-6">
            The group you're looking for doesn't exist or has been removed.
          </p>
          <Button onClick={() => navigate("/dashboard/groups")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Groups
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  const handleRemoveMember = (memberId: string) => {
    // Prevent removing the leader
    const isLeader =
      group.members.find((m) => m.id === memberId)?.role === "leader";
    if (isLeader) {
      toast.error("Cannot remove the group leader. Change the leader first.");
      return;
    }

    removeMemberMutation.mutate(memberId);
  };
  const canEdit = user?.role === "mentor" || user?.role === "admin";
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <GroupDetailHeader
          group={group}
          onBack={() => navigate("/dashboard/groups")}
          onDelete={() => setIsDeleteDialogOpen(true)}
          canManage={isMentor}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Members
              </CardTitle>
              <CardDescription>
                {group.members.length} member
                {group.members.length !== 1 ? "s" : ""} in this group
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {isMentor && (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsAddMemberDialogOpen(true)}
                    >
                      <UserPlus className="mr-2 h-4 w-4" />
                      Add Member
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsChangeLeaderDialogOpen(true)}
                    >
                      Change Leader
                    </Button>
                  </div>
                )}

                <GroupMemberList
                  members={group.members}
                  onRemoveMember={isMentor ? handleRemoveMember : undefined}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>
                Information about the associated project
              </CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">
                    Project Title
                  </dt>
                  <dd className="mt-1 text-sm">{group.projectTitle}</dd>
                </div>
                {group.description && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">
                      Description
                    </dt>
                    <dd className="mt-1 text-sm">{group.description}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">
                    Progress
                  </dt>
                  <dd className="mt-1 text-sm">{progress}% complete</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">
                    GitHub Link
                  </dt>
                  <dd className="mt-1 text-sm">
                    {group.githubLink ? (
                      <a
                        href={group.githubLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline hover:text-blue-800"
                      >
                        {group.githubLink}
                      </a>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsAddGitHubDialogOpen(true)}
                      >
                        Add GitHub Link
                      </Button>
                    )}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>
      </div>
      {!isEditing && (
        <Tabs
          defaultValue="tasks"
          className="w-full mt-6"
          onValueChange={(tab) => {
            if (tab === "free_rider") fetchFreeRiders();
          }}
        >
          <TabsList className="flex w-full mb-4">
            <TabsTrigger value="tasks" className="flex-1">
              Tasks
            </TabsTrigger>
            <TabsTrigger value="commits" className="flex-1">
              GitHub Commits
            </TabsTrigger>
            <TabsTrigger value="free_rider" className="flex-1">
              Free Rider
            </TabsTrigger>
            <TabsTrigger value="evaluation" className="flex-1">
              Evaluation
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tasks">
            <div className="bg-card p-6 rounded-lg border">
              <TaskList tasks={taskss} projectId={projectId!} />
            </div>
          </TabsContent>
          <TabsContent value="commits">
            <div className="bg-card p-6 rounded-lg border">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">GitHub Commits</h2>
                <Button
                  variant="outline"
                  onClick={async () => {
                    if (group?.githubLink) {
                      try {
                        // Tách username và repo_name từ link GitHub
                        const githubUrl = new URL(group.githubLink);
                        const pathParts = githubUrl.pathname
                          .split("/")
                          .filter(Boolean);
                        if (pathParts.length < 2) {
                          toast.error("Invalid GitHub link format.");
                          return;
                        }

                        const username = pathParts[0];
                        const repoName = pathParts[1];

                        const commitData = await getGitHubCommits(
                          username,
                          repoName
                        );
                        setCommits(commitData);
                        toast.success("Commits fetched successfully!");
                      } catch (error) {
                        console.error("Error fetching GitHub commits:", error);
                        toast.error("Failed to fetch commits.");
                      }
                    } else {
                      toast.error(
                        "GitHub link is not available. Please add a GitHub link first."
                      );
                    }
                  }}
                >
                  Fetch Commits
                </Button>
              </div>
              {commits.length > 0 ? (
                <div className="space-y-4">
                  {commits.map((commit, index) => (
                    <div
                      key={index}
                      className="border rounded-lg p-4 bg-muted/60 hover:shadow-md transition flex flex-col gap-2"
                    >
                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-primary">
                            {commit.author}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(commit.date).toLocaleString()}
                          </span>
                        </div>
                        <a
                          href={commit.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 underline hover:text-blue-800"
                        >
                          View Commit
                        </a>
                      </div>
                      <div className="mt-1">
                        <span className="font-medium text-secondary-foreground">
                          {commit.message}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center">
                  No commits found.
                </p>
              )}
            </div>
          </TabsContent>
          <TabsContent value="free_rider">
            <div className="bg-card p-6 rounded-lg border">
              <div className="space-y-2">
                {isLoadingFreeRider ? (
                  <p className="text-muted-foreground text-center">
                    Loading...
                  </p>
                ) : freeRiders.length === 0 ? (
                  <p className="text-muted-foreground text-center">
                    No free riders found.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="py-2 px-3 border-b text-center">#</th>
                          <th className="py-2 px-3 border-b text-center">
                            Avatar
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Name
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Email
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Score
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Commits
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Lines Added
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Lines Removed
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Files Modified
                          </th>
                          <th className="py-2 px-3 border-b text-center">
                            Last Commit
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {freeRiders.map((member, idx) => (
                          <tr
                            key={member.id}
                            className="hover:bg-gray-100 transition-colors border-b last:border-b-0"
                          >
                            <td className="py-2 px-3 text-center">{idx + 1}</td>
                            <td className="py-2 px-3 text-center">
                              {member.avatar && (
                                <img
                                  src={member.avatar}
                                  alt={member.name}
                                  className="w-8 h-8 rounded-full object-cover mx-auto"
                                />
                              )}
                            </td>
                            <td className="py-2 px-3 text-center font-medium">
                              {member.name}
                            </td>
                            <td className="py-2 px-3 text-center ">
                              {member.email}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.score ?? "-"}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.commit_count ?? "-"}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.lines_added ?? "-"}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.lines_removed ?? "-"}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.files_modified ?? "-"}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {member.last_commit_date
                                ? new Date(
                                    member.last_commit_date
                                  ).toLocaleString()
                                : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="evaluation">
            <div className="bg-card p-6 rounded-lg border">
              <GroupEvaluationTab group={group} />
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* Delete Group Dialog */}
      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              group "{group.name}" and remove all members from it.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteGroupMutation.mutate()}
              className="bg-destructive text-destructive-foreground"
            >
              {deleteGroupMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Add Member Dialog */}
      <AddMemberDialog
        open={isAddMemberDialogOpen}
        onOpenChange={setIsAddMemberDialogOpen}
        onAddMember={(member) => addMemberMutation.mutate(member)}
        existingMemberIds={group.members.map((m) => m.id)}
        isLoading={addMemberMutation.isPending}
      />

      {/* Change Leader Dialog */}
      <ChangeLeaderDialog
        open={isChangeLeaderDialogOpen}
        onOpenChange={setIsChangeLeaderDialogOpen}
        members={group.members}
        currentLeaderId={
          group.members.find((m) => m.role === "leader")?.id || ""
        }
        onChangeLeader={(newLeaderId) =>
          changeLeaderMutation.mutate(newLeaderId)
        }
        isLoading={changeLeaderMutation.isPending}
      />

      {/* Add GitHub Link Dialog */}
      <AlertDialog
        open={isAddGitHubDialogOpen}
        onOpenChange={setIsAddGitHubDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Add GitHub Link</AlertDialogTitle>
            <AlertDialogDescription>
              Please enter the GitHub repository link for this project.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Enter GitHub Link"
              value={githubLinkInput}
              onChange={(e) => setGitHubLinkInput(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (githubLinkInput.trim()) {
                  updateGitHubLinkMutation.mutate(githubLinkInput.trim());
                } else {
                  toast.error("GitHub link cannot be empty");
                }
              }}
            >
              Add Link
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  );
};

export default GroupDetail;
