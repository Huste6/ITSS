import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/layout/DashboardLayout";
import { getAll } from "../data/userData";
import { Avatar, AvatarImage, AvatarFallback } from "../components/ui/avatar";
// import { useState } from "react";
import { Pencil, Trash } from "lucide-react";

type UserRole = "admin" | "mentor" | "student";
type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  // add other properties if needed
};

const AdminUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const data = await getAll();
        // Sắp xếp: admin lên đầu, mentor tiếp theo, student cuối
        const roleOrder: Record<UserRole, number> = {
          admin: 0,
          mentor: 1,
          student: 2,
        };
        const sorted = [...(data as User[])].sort((a, b) => {
          return (roleOrder[a.role] ?? 3) - (roleOrder[b.role] ?? 3);
        });
        setUsers(sorted);
      } catch (err) {
        setError("Failed to fetch users");
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight mb-4 text-center">
          User Management
        </h1>
        {loading ? (
          <div className="text-center text-lg">Loading...</div>
        ) : error ? (
          <div className="text-red-500 text-center">{error}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-md">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-3 px-4 border-b text-center">#</th>
                  <th className="py-3 px-4 border-b text-center">Avatar</th>
                  <th className="py-3 px-4 border-b text-center">Name</th>
                  <th className="py-3 px-4 border-b text-center">Email</th>
                  <th className="py-3 px-4 border-b text-center">Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, idx) => (
                  <tr
                    key={user.id}
                    className="hover:bg-gray-100 transition-colors border-b last:border-b-0"
                  >
                    <td className="py-2 px-4 text-center font-semibold text-gray-700">
                      {idx + 1}
                    </td>
                    <td className="py-2 px-4 text-center">
                      <Avatar className="mx-auto h-10 w-10">
                        <AvatarImage src={user.avatar} alt={user.name} />
                        <AvatarFallback>
                          {user.name?.charAt(0) || "U"}
                        </AvatarFallback>
                      </Avatar>
                    </td>
                    <td className="py-2 px-4 text-center text-gray-900 font-medium">
                      {user.name}
                    </td>
                    <td className="py-2 px-4 text-center text-gray-700">
                      {user.email}
                    </td>
                    <td className="py-2 px-4 text-center">
                      <span
                        className={
                          user.role === "admin"
                            ? "inline-block rounded-full bg-red-100 text-red-700 px-3 py-1 text-xs font-semibold"
                            : user.role === "mentor"
                            ? "inline-block rounded-full bg-yellow-100 text-yellow-800 px-3 py-1 text-xs font-semibold"
                            : "inline-block rounded-full bg-blue-100 text-blue-700 px-3 py-1 text-xs font-semibold"
                        }
                      >
                        {user.role}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminUsers;
