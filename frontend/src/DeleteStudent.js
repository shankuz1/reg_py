import React, { useState } from 'react';

function DeleteStudent() {
  const [email, setEmail]         = useState('');
  const [firstName, setFirstName] = useState('');
  const [message, setMessage]     = useState('');

  const handleDelete = async (e) => {
    e.preventDefault();
    setMessage('');

    try {
      const response = await fetch('http://localhost:3002/deleteUser', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, firstName })
      });

      if (!response.ok) {
        const errorData = await response.json();
        setMessage(errorData.error || 'Error deleting student');
      } else {
        const data = await response.json();
        setMessage(data.message);
        setEmail('');
        setFirstName('');
      }
    } catch (error) {
      console.error(error);
      setMessage('An error occurred while deleting the student');
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-md shadow-md">
      <h2 className="text-2xl font-bold mb-4">Delete Student</h2>
      <form onSubmit={handleDelete} className="space-y-4">
        <div>
          <label className="block font-semibold mb-1">Email</label>
          <input 
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none"
          />
        </div>
        <div>
          <label className="block font-semibold mb-1">First Name</label>
          <input 
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none"
          />
        </div>
        <button 
          type="submit"
          className="bg-red-600 text-white font-semibold py-2 px-4 rounded hover:bg-red-700 transition-colors"
        >
          Delete
        </button>
      </form>

      {message && (
        <p className="mt-4 font-semibold">
          {message}
        </p>
      )}
    </div>
  );
}

export default DeleteStudent;
