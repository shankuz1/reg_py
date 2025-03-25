import React, { useEffect, useState } from 'react';

function ViewStudents() {
  const [students, setStudents] = useState([]);
  const [error, setError]       = useState('');

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await fetch('http://localhost:3002/students');
      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.error || 'Error fetching students');
      } else {
        const data = await response.json();
        setStudents(data);
        setError('');
      }
    } catch (err) {
      console.error(err);
      setError('An error occurred while fetching students');
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white p-6 rounded-md shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">All Students</h2>
        <button 
          onClick={fetchStudents} 
          className="bg-green-600 text-white font-semibold px-4 py-2 rounded hover:bg-green-700"
        >
          Refresh
        </button>
      </div>

      {error && (
        <p className="text-red-600 font-semibold mb-4">
          {error}
        </p>
      )}

      {students.length === 0 && !error && (
        <p>No students found.</p>
      )}

      <ul className="divide-y divide-gray-200">
        {students.map((student) => (
          <li key={student.id} className="py-3">
            <p className="font-semibold">
              {student.firstName} {student.lastName}
            </p>
            <p>{student.email}</p>
            <p className="text-gray-500">{student.dob}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ViewStudents;
