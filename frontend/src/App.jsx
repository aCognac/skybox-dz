import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <div>
      <h1>Skybox DZ</h1>
      <p>Backend: {status ?? "checking…"}</p>
    </div>
  );
}
