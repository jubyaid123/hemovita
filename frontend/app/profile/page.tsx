import { getServerAuthSession } from "@/lib/auth";
import { redirect } from "next/navigation";
import { ProfileForm } from "@/components/profile/profile-form";

export default async function ProfilePage() {
  const session = await getServerAuthSession();

  if (!session?.user) {
    redirect("/sign-in");
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">Your Profile</h1>
      <ProfileForm user={session.user} />
    </div>
  );
}
