import SupportForm from "@/components/SupportForm";

export default function Home() {
  return (
    <main className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          TaskFlow Pro Support
        </h1>
        <p className="text-gray-500">
          24/7 AI-powered customer support
        </p>
      </div>
      <SupportForm apiEndpoint="/api/support/submit" />
    </main>
  );
}
