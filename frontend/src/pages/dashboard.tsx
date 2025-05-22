import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { TaskCard, Task } from "../components/tasks/TaskCard";
import { ProjectCard, Project } from "../components/projects/ProjectCard";
import { GroupCard, Group } from "../components/groups/GroupCard";
import { Button } from "../components/ui/button";
import { Link } from "react-router-dom";
import { getProjects } from "../data/projectsData";
import { getGroups } from "../data/groupData";
import axiosInstance from "../axios-config";
import { getTasks } from "../data/taskData";
import Tasks from "./Tasks";
const Dashboard = () => {
  const { user } = useAuth();
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);

  // Mock data loading
  useEffect(() => {
    // Mock tasks data
    const loadTasks = async () => {
      try {
        const taskData = await getTasks();
        setRecentTasks(taskData);
        console.log("Tasks state updated:", taskData);
      } catch (error) {
        console.error("Error loading tasks:", error);
        // Có thể thêm thông báo lỗi cho người dùng
      }
    };
    if (user?.id) {
      loadTasks();
    }
    const loadProjects = async () => {
      try {
        const projectsData = await getProjects();
        setProjects(projectsData);
        console.log("Projects state updated:", projectsData);
      } catch (error) {
        console.error("Error loading projects:", error);
      }
    };

    if (user?.id) {
      loadProjects();
    }

    const loadGroups = async () => {
      try {
        console.log("Loading projects...");
        const projectsData = await getGroups();
        setGroups(projectsData);
        console.log("Projects state updated:", projectsData);
      } catch (error) {
        console.error("Error loading projects:", error);
        // Có thể thêm thông báo lỗi cho người dùng
      }
    };
    if (user?.id) {
      loadGroups();
    }
  }, [user?.id]);
  const randomIndex = Math.floor(Math.random() * projects.length);
  const randomIndexForGroup = Math.floor(Math.random() * groups.length);
  const randomIndexForTask = Math.floor(Math.random() * recentTasks.length);
  let randomIndexForTask2 = Math.floor(Math.random() * recentTasks.length);
  while (randomIndexForTask2 === randomIndexForTask && recentTasks.length > 1) {
    randomIndexForTask2 = Math.floor(Math.random() * recentTasks.length);
  }
  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.name}
          </h1>
          <p className="text-muted-foreground">
            Here's an overview of your academic collaboration activities
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Projects</CardTitle>
              <CardDescription className="text-2xl font-bold">
                {projects.length}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {user?.role === "mentor"
                  ? "Projects you're mentoring"
                  : "Projects you're working on"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Groups</CardTitle>
              <CardDescription className="text-2xl font-bold">
                {groups.length}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {user?.role === "mentor"
                  ? "Groups you're supervising"
                  : user?.role === "leader"
                  ? "Groups you're leading"
                  : "Groups you're a member of"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Tasks</CardTitle>
              <CardDescription className="text-2xl font-bold">
                {recentTasks.length}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Active tasks assigned to you
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Upcoming Deadlines
              </CardTitle>
              <CardDescription className="text-2xl font-bold">
                {
                  recentTasks.filter(
                    (task) =>
                      new Date(task.dueDate).getTime() - new Date().getTime() <
                      7 * 24 * 60 * 60 * 1000
                  ).length
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Tasks due within a week
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Tasks */}
        <Card>
          <CardHeader>
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
          </CardHeader>
          <CardContent>
            {recentTasks.length === 0 ? (
              <p className="text-center py-8 text-muted-foreground">
                No tasks assigned yet
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* {recentTasks.map((task) => (
                  <TaskCard key={task.id} task={task} />
                ))}
                <ProjectCard project={projects[randomIndex]} /> */}
                <TaskCard task={recentTasks[randomIndexForTask]}></TaskCard>
                <TaskCard task={recentTasks[randomIndexForTask2]}></TaskCard>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Projects & Groups */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Projects */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Projects</CardTitle>
                  <CardDescription>
                    {user?.role === "mentor"
                      ? "Projects you're mentoring"
                      : "Projects you're involved in"}
                  </CardDescription>
                </div>
                <Button asChild>
                  <Link to="/dashboard/projects">View All</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {projects.length === 0 ? (
                <p className="text-center py-8 text-muted-foreground">
                  No projects found
                </p>
              ) : (
                <div className="space-y-4">
                  {/* {projects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))} */}
                  <ProjectCard project={projects[randomIndex]} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Groups */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Groups</CardTitle>
                  <CardDescription>Your project groups</CardDescription>
                </div>
                <Button asChild>
                  <Link to="/dashboard/groups">View All</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {groups.length === 0 ? (
                <p className="text-center py-8 text-muted-foreground">
                  No groups found
                </p>
              ) : (
                <div className="space-y-4">
                  <GroupCard group={groups[randomIndexForGroup]}></GroupCard>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
