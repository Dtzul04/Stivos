import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8001";

type DanceClass = {
  id: number;
  name: string;
  instructor: string;
  start_time: string;
  capacity: number;
  spots_remaining: number;
};

type Student = {
  id: number;
  name: string;
  email: string;
};

type Booking = {
  id: number;
  student_id: number;
  class_id: number;
  status: "booked" | "waitlisted" | "cancelled";
  created_at: string;
};

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

function formatWhen(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

export default function App() {
  const [classes, setClasses] = useState<DanceClass[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [studentId, setStudentId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [classResponse, studentResponse, bookingResponse] = await Promise.all([
      fetch(`${API}/classes`),
      fetch(`${API}/students`),
      fetch(`${API}/bookings`),
    ]);
    if (!classResponse.ok || !studentResponse.ok || !bookingResponse.ok) {
      throw new Error("Could not load the studio.");
    }
    const [classRows, studentRows, bookingRows] = (await Promise.all([
      classResponse.json(),
      studentResponse.json(),
      bookingResponse.json(),
    ])) as [DanceClass[], Student[], Booking[]];
    setClasses(classRows);
    setStudents(studentRows);
    setBookings(bookingRows);
    setStudentId((current) => current || (studentRows[0]?.id ?? ""));
  }, []);

  useEffect(() => {
    load().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Could not load the studio.");
    });
  }, [load]);

  async function book(classId: number) {
    if (studentId === "") {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`${API}/bookings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, class_id: classId }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Booking failed.");
    } finally {
      setBusy(false);
    }
  }

  async function cancel(bookingId: number) {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`${API}/bookings/${bookingId}/cancel`, { method: "POST" });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Cancel failed.");
    } finally {
      setBusy(false);
    }
  }

  const studentName = new Map(students.map((student) => [student.id, student.name]));
  const className = new Map(classes.map((danceClass) => [danceClass.id, danceClass.name]));
  const openBookings = bookings.filter((booking) => booking.status !== "cancelled");

  return (
    <div className="shell">
      <header className="brand">
        <h1>Stivos</h1>
        <p>The next big thing, for the long term.</p>
      </header>

      {error ? <p className="error">{error}</p> : null}

      <section className="panel" aria-labelledby="who-heading">
        <h2 id="who-heading">Who is booking</h2>
        <p className="panel-lead">Choose the student for the next Book click.</p>
        <label className="field">
          Student
          <select
            value={studentId}
            onChange={(event) => setStudentId(Number(event.target.value))}
          >
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.name}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="panel" aria-labelledby="classes-heading">
        <h2 id="classes-heading">Classes</h2>
        <p className="panel-lead">Open spots fill first. A full class waitlists you.</p>
        <ul className="list">
          {classes.map((danceClass, index) => (
            <li
              key={danceClass.id}
              className="row"
              style={{ animationDelay: `${0.04 * index}s` }}
            >
              <strong>{danceClass.name}</strong>
              <span className="meta">
                {danceClass.instructor} · {formatWhen(danceClass.start_time)} ·{" "}
                {danceClass.spots_remaining} of {danceClass.capacity} left
              </span>
              <button
                type="button"
                className="primary"
                disabled={busy || studentId === ""}
                onClick={() => book(danceClass.id)}
              >
                Book
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel" aria-labelledby="bookings-heading">
        <h2 id="bookings-heading">Bookings</h2>
        <p className="panel-lead">Cancel a booked spot to promote the oldest waitlisted student.</p>
        {openBookings.length === 0 ? <p className="empty">No bookings yet.</p> : null}
        <ul className="list">
          {openBookings.map((booking, index) => (
            <li
              key={booking.id}
              className="row"
              style={{ animationDelay: `${0.04 * index}s` }}
            >
              <strong>{studentName.get(booking.student_id) ?? "Student"}</strong>
              <span className="meta">
                {className.get(booking.class_id) ?? "Class"}
                <span className={`status ${booking.status}`}>{booking.status}</span>
              </span>
              <button
                type="button"
                className="ghost"
                disabled={busy}
                onClick={() => cancel(booking.id)}
              >
                Cancel
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
