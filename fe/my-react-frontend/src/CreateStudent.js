import React, { useState } from 'react';

function CreateStudent() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName]   = useState('');
  const [email, setEmail]         = useState('');
  const [dob, setDob]             = useState('');

  // We'll still keep a 'message' for debugging if you like
  const [message, setMessage]     = useState('');

  // This state determines if the modal is visible
  const [successModalOpen, setSuccessModalOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    try {
      const response = await fetch('http://localhost:3002/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ firstName, lastName, email, dob })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        setMessage(errorData.error || 'Error creating student');
      } else {
        const data = await response.json();
        setMessage(`Student created: ${data.firstName} ${data.lastName}`);

        // Clear form fields
        setFirstName('');
        setLastName('');
        setEmail('');
        setDob('');

        // Show the success modal
        setSuccessModalOpen(true);
      }
    } catch (error) {
      console.error(error);
      setMessage('An error occurred while creating student');
    }
  };

  // Function to close the modal
  const closeModal = () => {
    setSuccessModalOpen(false);
  };

  return (
    <div className="relative max-w-md mx-auto bg-white p-6 rounded-md shadow-md">
      <h2 className="text-2xl font-bold mb-4">Create Student</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
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
        <div>
          <label className="block font-semibold mb-1">Last Name</label>
          <input 
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none"
          />
        </div>
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
          <label className="block font-semibold mb-1">Date of Birth (YYYY-MM-DD)</label>
          <input 
            type="text"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none"
          />
        </div>
        <button 
          type="submit"
          className="bg-blue-600 text-white font-semibold py-2 px-4 rounded hover:bg-blue-700 transition-colors"
        >
          Register
        </button>
      </form>

      {message && (
        <p className="mt-4 text-sm text-gray-600 font-semibold">
          {message}
        </p>
      )}

      {/* SUCCESS MODAL OVERLAY */}
      {successModalOpen && (
        <div 
          className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
          onClick={closeModal} // Clicking outside also closes the modal
        >
          {/* Modal Content */}
          <div 
            className="bg-white p-6 rounded-md shadow-md"
            onClick={(e) => e.stopPropagation()} // Prevent close on modal content click
          >
            <h3 className="text-xl font-bold mb-2">Student Created</h3>
            <p className="text-gray-700 mb-4">The student has been successfully registered!</p>
            <button 
              onClick={closeModal}
              className="bg-green-500 text-white font-semibold py-2 px-4 rounded hover:bg-green-600 transition-colors"
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CreateStudent;
