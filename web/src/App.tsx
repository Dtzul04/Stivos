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
    <main>
      <h1>Stivos</h1>
      <p>Pick a student, book a class, or cancel a spot.</p>
      {error ? <p className="error">{error}</p> : null}

      <label>
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

      <h2>Classes</h2>
      <ul>
        {classes.map((danceClass) => (
          <li key={danceClass.id}>
            <strong>{danceClass.name}</strong>
            <span>
              {danceClass.instructor} · {danceClass.spots_remaining} of {danceClass.capacity} spots
              left
            </span>
            <button type="button" disabled={busy || studentId === ""} onClick={() => book(danceClass.id)}>
              Book
            </button>
          </li>
        ))}
      </ul>

      <h2>Bookings</h2>
      {openBookings.length === 0 ? <p>No bookings yet.</p> : null}
      <ul>
        {openBookings.map((booking) => (
          <li key={booking.id}>
            <strong>{studentName.get(booking.student_id) ?? "Student"}</strong>
            <span>
              {className.get(booking.class_id) ?? "Class"} · {booking.status}
            </span>
            <button type="button" disabled={busy} onClick={() => cancel(booking.id)}>
              Cancel
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
