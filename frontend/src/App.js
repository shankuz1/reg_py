import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link
} from 'react-router-dom';

import CreateStudent from './CreateStudent';
import DeleteStudent from './DeleteStudent';
import ViewStudents from './ViewStudents';

function App() {
  return (
    <Router>
      {/* A simple container for layout */}
      <div className="min-h-screen bg-gray-100 p-4">
        {/* NAVIGATION */}
        <nav className="bg-white p-4 rounded-md shadow-md mb-6">
          <ul className="flex space-x-4">
            <li>
              <Link 
                to="/create" 
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                Create Student
              </Link>
            </li>
            <li>
              <Link 
                to="/delete" 
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                Delete Student
              </Link>
            </li>
            <li>
              <Link 
                to="/students" 
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                View Students
              </Link>
            </li>
          </ul>
        </nav>

        {/* ROUTES */}
        <Routes>
          <Route path="/create" element={<CreateStudent />} />
          <Route path="/delete" element={<DeleteStudent />} />
          <Route path="/students" element={<ViewStudents />} />
          <Route path="/" element={
            <div className="text-center mt-20">
              <h2 className="text-2xl font-semibold mb-4">
                Welcome to the Student Management App
              </h2>
              <p>Select a menu option above to begin.</p>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
