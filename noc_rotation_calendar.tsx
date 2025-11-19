import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Users, Clock } from 'lucide-react';

const NOCRotationCalendar = () => {
  const [currentMonth, setCurrentMonth] = useState(0); // 0 = Nov 2025, 1 = Dec 2025, 2 = Jan 2026

  // Engineer schedule data
  const engineers = [
    { name: "Alexandra Hock", email: "alexandra.hock@ringcentral.com", schedule: { sun: "OFF", mon: "05:00-14:00", tue: "05:00-14:00", wed: "05:00-14:00", thu: "05:00-14:00", fri: "05:00-14:00", sat: "OFF" }, shift: "early" },
    { name: "Marina Stambaugh", email: "marina.stambaugh@ringcentral.com", schedule: { sun: "OFF", mon: "07:00-16:00", tue: "07:00-16:00", wed: "07:00-16:00", thu: "07:00-16:00", fri: "07:00-16:00", sat: "OFF" }, shift: "early" },
    { name: "Rochelle Gobis", email: "rochelle.gobis@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-15:30", tue: "08:00-15:30", wed: "08:00-15:30", thu: "08:00-15:30", fri: "08:00-15:30", sat: "OFF" }, shift: "day" },
    { name: "Sarah Heriford", email: "sarah.heriford@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-16:30", tue: "08:00-16:30", wed: "08:00-16:30", thu: "08:00-16:30", fri: "08:00-16:30", sat: "OFF" }, shift: "day" },
    { name: "Karla Talamantes", email: "karla.talamantes@ringcentral.com", schedule: { sun: "OFF", mon: "09:00-18:00", tue: "09:00-18:00", wed: "09:00-18:00", thu: "09:00-18:00", fri: "09:00-18:00", sat: "OFF" }, shift: "day" },
    { name: "Jeremy Rodriguez", email: "jeremyr@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-16:30", tue: "08:00-16:30", wed: "08:00-16:30", thu: "08:00-16:30", fri: "08:00-16:30", sat: "OFF" }, shift: "day" },
    { name: "Jenny Deasy", email: "jenny.deasy@ringcentral.com", schedule: { sun: "OFF", mon: "07:00-15:30", tue: "07:00-15:30", wed: "07:00-15:30", thu: "07:00-15:30", fri: "07:00-15:30", sat: "OFF" }, shift: "early" },
    { name: "Bo Lemecha", email: "Bo.Lemecha@ringcentral.com", schedule: { sun: "OFF", mon: "06:00-14:30", tue: "06:00-14:30", wed: "06:00-14:30", thu: "06:00-14:30", fri: "06:00-14:30", sat: "OFF" }, shift: "early" },
    { name: "Edwin Reveley", email: "edwin.reveley@ringcentral.com", schedule: { sun: "OFF", mon: "09:30-18:00", tue: "09:30-18:00", wed: "09:30-18:00", thu: "09:30-18:00", fri: "09:30-18:00", sat: "OFF" }, shift: "day" },
    { name: "Edward Salvador", email: "edward.salvador@ringcentral.com", schedule: { sun: "08:00-15:30", mon: "08:00-15:30", tue: "08:00-15:30", wed: "08:00-15:30", thu: "08:00-15:30", fri: "OFF", sat: "OFF" }, shift: "day" },
    { name: "John Glenn Bayron", email: "john.bayron@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-15:30", tue: "08:00-15:30", wed: "08:00-15:30", thu: "08:00-15:30", fri: "08:00-15:30", sat: "OFF" }, shift: "day" },
    { name: "Robert Carter", email: "robert.carter@ringcentral.com", schedule: { sun: "OFF", mon: "09:00-17:00", tue: "09:00-17:00", wed: "09:00-17:00", thu: "09:00-17:00", fri: "09:00-17:00", sat: "OFF" }, shift: "day" },
    { name: "Dan Baker", email: "dan.baker1@ringcentral.com", schedule: { sun: "OFF", mon: "07:00-15:00", tue: "07:00-15:00", wed: "07:00-15:00", thu: "07:00-15:00", fri: "07:00-15:00", sat: "OFF" }, shift: "early" },
    { name: "John Tran", email: "john.tran@ringcentral.com", schedule: { sun: "OFF", mon: "10:00-18:00", tue: "10:00-18:00", wed: "10:00-18:00", thu: "10:00-18:00", fri: "10:00-18:00", sat: "OFF" }, shift: "day" },
    { name: "Jared Cooper", email: "jared.cooper@ringcentral.com", schedule: { sun: "OFF", mon: "09:00-18:00", tue: "09:00-18:00", wed: "09:00-18:00", thu: "09:00-18:00", fri: "09:00-18:00", sat: "OFF" }, shift: "day" },
    { name: "Lara Mae Dela Cruz", email: "lara.delacruz@ringcentral.com", schedule: { sun: "OFF", mon: "15:00-00:00", tue: "15:00-00:00", wed: "15:00-00:00", thu: "15:00-00:00", fri: "15:00-00:00", sat: "OFF" }, shift: "evening" },
    { name: "Love Lyn Cano", email: "love.cano@ringcentral.com", schedule: { sun: "15:00-00:00", mon: "15:00-00:00", tue: "15:00-00:00", wed: "15:00-00:00", thu: "OFF", fri: "OFF", sat: "15:00-00:00" }, shift: "evening" },
    { name: "James Belleza", email: "james.belleza@ringcentral.com", schedule: { sun: "15:00-00:00", mon: "15:00-00:00", tue: "15:00-00:00", wed: "15:00-00:00", thu: "15:00-00:00", fri: "OFF", sat: "OFF" }, shift: "evening" },
    { name: "Rushikesh Sawant", email: "rushikesh.sawant@ringcentral.com", schedule: { sun: "22:30-07:30", mon: "22:30-07:30", tue: "22:30-07:30", wed: "22:30-07:30", thu: "22:30-07:30", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Santosh Sahoo", email: "santosh.sahoo@ringcentral.com", schedule: { sun: "22:30-07:30", mon: "22:30-07:30", tue: "22:30-07:30", wed: "22:30-07:30", thu: "22:30-07:30", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Srikanth Reddy", email: "srikanth.v@ringcentral.com", schedule: { sun: "22:30-07:30", mon: "22:30-07:30", tue: "22:30-07:30", wed: "22:30-07:30", thu: "22:30-07:30", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Jobon Chinel", email: "jobon.chinel@ringcentral.com", schedule: { sun: "01:00-10:00", mon: "01:00-10:00", tue: "01:00-10:00", wed: "01:00-10:00", thu: "01:00-10:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Ryan Hawkins", email: "ryan.hawkins@ringcentral.com", schedule: { sun: "01:00-07:00", mon: "01:00-07:00", tue: "01:00-07:00", wed: "01:00-07:00", thu: "01:00-07:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Joseph Bendecio", email: "joseph.bendecio@ringcentral.com", schedule: { sun: "OFF", mon: "OFF", tue: "01:00-10:00", wed: "01:00-10:00", thu: "01:00-10:00", fri: "01:00-10:00", sat: "01:00-10:00" }, shift: "night" },
    { name: "Pearce Hamblin", email: "pearce.hamblin@ringcentral.com", schedule: { sun: "01:00-07:00", mon: "01:00-07:00", tue: "01:00-07:00", wed: "01:00-07:00", thu: "01:00-07:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Amine Dahel", email: "amine.dahel@ringcentral.com", schedule: { sun: "00:00-06:00", mon: "00:00-06:00", tue: "00:00-06:00", wed: "00:00-06:00", thu: "00:00-06:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Andrew Neill", email: "andrew.neill@ringcentral.com", schedule: { sun: "03:00-09:00", mon: "03:00-09:00", tue: "03:00-09:00", wed: "03:00-09:00", thu: "03:00-09:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Andy Connolly", email: "andy.connolly@ringcentral.com", schedule: { sun: "03:00-09:00", mon: "03:00-09:00", tue: "03:00-09:00", wed: "03:00-09:00", thu: "03:00-09:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Colin Finn", email: "colin.finn@ringcentral.com", schedule: { sun: "02:00-08:00", mon: "02:00-08:00", tue: "02:00-08:00", wed: "02:00-08:00", thu: "02:00-08:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Deepthi Chandran", email: "deepthi.chandran@ringcentral.com", schedule: { sun: "00:00-06:00", mon: "00:00-06:00", tue: "00:00-06:00", wed: "00:00-06:00", thu: "00:00-06:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Derek Walker", email: "derek.walker@ringcentral.com", schedule: { sun: "00:00-06:00", mon: "00:00-06:00", tue: "00:00-06:00", wed: "00:00-06:00", thu: "00:00-06:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Hugo Nickal-Thibeaud", email: "hugo.thibeaud@ringcentral.com", schedule: { sun: "02:00-08:00", mon: "02:00-08:00", tue: "02:00-08:00", wed: "02:00-08:00", thu: "02:00-08:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Baranee Selvendran", email: "baranee.selvendran@ringcentral.com", schedule: { sun: "02:00-10:00", mon: "02:00-10:00", tue: "02:00-10:00", wed: "02:00-10:00", thu: "02:00-10:00", fri: "OFF", sat: "OFF" }, shift: "night" },
    { name: "Eryll Azucena", email: "eryll.azucena@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-15:30", tue: "08:00-15:30", wed: "08:00-15:30", thu: "08:00-15:30", fri: "08:00-15:30", sat: "08:00-15:30" }, shift: "day" },
    { name: "Mare Snyder", email: "mare.snyder@ringcentral.com", schedule: { sun: "OFF", mon: "09:00-18:00", tue: "09:00-18:00", wed: "09:00-18:00", thu: "09:00-18:00", fri: "09:00-18:00", sat: "OFF" }, shift: "day" },
    { name: "Nate Malone", email: "nate.malone@ringcentral.com", schedule: { sun: "OFF", mon: "07:00-16:00", tue: "07:00-16:00", wed: "07:00-16:00", thu: "07:00-16:00", fri: "07:00-16:00", sat: "OFF" }, shift: "early" },
    { name: "Peter Czarnecki", email: "peter.czarnecki@ringcentral.com", schedule: { sun: "OFF", mon: "06:00-14:30", tue: "06:00-14:30", wed: "06:00-14:30", thu: "06:00-14:30", fri: "06:00-14:30", sat: "OFF" }, shift: "early" },
    { name: "Colby Jestes", email: "colby.jestes@ringcentral.com", schedule: { sun: "OFF", mon: "08:00-16:30", tue: "08:00-16:30", wed: "08:00-16:30", thu: "08:00-16:30", fri: "08:00-16:30", sat: "OFF" }, shift: "day" },
    { name: "Mark Peirce", email: "mark.peirce@ringcentral.com", schedule: { sun: "09:00-18:00", mon: "09:00-18:00", tue: "09:00-18:00", wed: "09:00-18:00", thu: "09:00-18:00", fri: "09:00-18:00", sat: "OFF" }, shift: "day" },
    { name: "Roscoe Bryant", email: "roscoe.bryant@ringcentral.com", schedule: { sun: "OFF", mon: "08:30-17:00", tue: "08:30-17:00", wed: "08:30-17:00", thu: "08:30-17:00", fri: "08:30-17:00", sat: "OFF" }, shift: "day" },
    { name: "Cindy Hubert", email: "cindy.hubert@ringcentral.com", schedule: { sun: "OFF", mon: "07:00-16:00", tue: "07:00-16:00", wed: "07:00-16:00", thu: "07:00-16:00", fri: "07:00-16:00", sat: "OFF" }, shift: "early" },
    { name: "Abby Bearden", email: "abby.bearden@ringcentral.com", schedule: { sun: "OFF", mon: "06:00-15:00", tue: "06:00-15:00", wed: "06:00-15:00", thu: "06:00-15:00", fri: "06:00-15:00", sat: "OFF" }, shift: "early" },
    { name: "Tim Arnott", email: "tim.arnott@ringcentral.com", schedule: { sun: "OFF", mon: "06:00-15:00", tue: "06:00-15:00", wed: "06:00-15:00", thu: "06:00-15:00", fri: "06:00-15:00", sat: "OFF" }, shift: "early" },
    { name: "Tomislav Vranjes", email: "tomislav.vranjes@ringcentral.com", schedule: { sun: "OFF", mon: "09:30-18:00", tue: "09:30-18:00", wed: "09:30-18:00", thu: "09:30-18:00", fri: "09:30-18:00", sat: "OFF" }, shift: "day" }
  ];

  // Helper function to check if engineer is working on a specific day
  const isWorking = (engineer, dayOfWeek) => {
    const days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
    return engineer.schedule[days[dayOfWeek]] !== "OFF";
  };

  // Generate rotation assignments
  const generateRotation = useMemo(() => {
    const rotation = {};
    const startDate = new Date(2025, 10, 18); // Nov 18, 2025 (month is 0-indexed)
    
    // Organize engineers by shift and create rotation pools
    const shiftPools = {
      early: engineers.filter(e => e.shift === 'early'),
      day: engineers.filter(e => e.shift === 'day'),
      evening: engineers.filter(e => e.shift === 'evening'),
      night: engineers.filter(e => e.shift === 'night')
    };

    // Rotation indices for each shift
    const rotationIndex = { early: 0, day: 0, evening: 0, night: 0 };

    // Generate 60 days of rotation
    for (let i = 0; i < 60; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const dayOfWeek = date.getDay();
      const dateKey = date.toISOString().split('T')[0];

      rotation[dateKey] = {};

      // Assign for each shift
      Object.keys(shiftPools).forEach(shift => {
        const pool = shiftPools[shift];
        const availableEngineers = pool.filter(eng => isWorking(eng, dayOfWeek));
        
        if (availableEngineers.length > 0) {
          // Rotate through available engineers
          const assignedEngineer = availableEngineers[rotationIndex[shift] % availableEngineers.length];
          rotation[dateKey][shift] = assignedEngineer;
          rotationIndex[shift]++;
        }
      });
    }

    return rotation;
  }, []);

  // Get calendar data for current month
  const getCalendarData = () => {
    const baseDate = new Date(2025, 10, 1); // Nov 1, 2025
    baseDate.setMonth(baseDate.getMonth() + currentMonth);
    
    const year = baseDate.getFullYear();
    const month = baseDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const monthNames = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];

    return {
      monthName: monthNames[month],
      year,
      daysInMonth,
      startingDayOfWeek,
      month
    };
  };

  const calendarData = getCalendarData();
  const [selectedDate, setSelectedDate] = useState(null);

  const renderCalendar = () => {
    const days = [];
    const { daysInMonth, startingDayOfWeek, year, month } = calendarData;

    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(<div key={`empty-${i}`} className="p-2 border border-gray-100"></div>);
    }

    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateKey = date.toISOString().split('T')[0];
      const assignments = generateRotation[dateKey] || {};
      const isToday = dateKey === new Date(2025, 10, 18).toISOString().split('T')[0];

      days.push(
        <div
          key={day}
          onClick={() => setSelectedDate(dateKey)}
          className={`p-2 border border-gray-200 min-h-24 cursor-pointer hover:bg-blue-50 transition-colors ${
            isToday ? 'bg-blue-100 border-blue-400' : ''
          } ${selectedDate === dateKey ? 'ring-2 ring-blue-500' : ''}`}
        >
          <div className={`font-semibold text-sm mb-1 ${isToday ? 'text-blue-700' : 'text-gray-700'}`}>
            {day}
          </div>
          <div className="text-xs space-y-1">
            {assignments.night && (
              <div className="bg-indigo-100 text-indigo-800 px-1 py-0.5 rounded truncate" title={`Night: ${assignments.night.name}`}>
                🌙 {assignments.night.name.split(' ')[0]}
              </div>
            )}
            {assignments.early && (
              <div className="bg-amber-100 text-amber-800 px-1 py-0.5 rounded truncate" title={`Early: ${assignments.early.name}`}>
                🌅 {assignments.early.name.split(' ')[0]}
              </div>
            )}
            {assignments.day && (
              <div className="bg-green-100 text-green-800 px-1 py-0.5 rounded truncate" title={`Day: ${assignments.day.name}`}>
                ☀️ {assignments.day.name.split(' ')[0]}
              </div>
            )}
            {assignments.evening && (
              <div className="bg-purple-100 text-purple-800 px-1 py-0.5 rounded truncate" title={`Evening: ${assignments.evening.name}`}>
                🌆 {assignments.evening.name.split(' ')[0]}
              </div>
            )}
          </div>
        </div>
      );
    }

    return days;
  };

  const renderSelectedDateDetails = () => {
    if (!selectedDate) return null;

    const assignments = generateRotation[selectedDate] || {};
    const date = new Date(selectedDate);
    const dateString = date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    return (
      <div className="mt-6 bg-white border-2 border-blue-200 rounded-lg p-4 shadow-lg">
        <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          {dateString}
        </h3>
        <div className="space-y-3">
          {assignments.night && (
            <div className="border-l-4 border-indigo-500 pl-3 py-2 bg-indigo-50 rounded">
              <div className="font-semibold text-indigo-900">🌙 Night Shift (00:00-10:00)</div>
              <div className="text-sm text-indigo-800">{assignments.night.name}</div>
              <div className="text-xs text-indigo-600">{assignments.night.email}</div>
              <div className="text-xs text-indigo-700 mt-1">
                Hours: {assignments.night.schedule[['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][date.getDay()]]}
              </div>
            </div>
          )}
          {assignments.early && (
            <div className="border-l-4 border-amber-500 pl-3 py-2 bg-amber-50 rounded">
              <div className="font-semibold text-amber-900">🌅 Early Shift (05:00-09:00)</div>
              <div className="text-sm text-amber-800">{assignments.early.name}</div>
              <div className="text-xs text-amber-600">{assignments.early.email}</div>
              <div className="text-xs text-amber-700 mt-1">
                Hours: {assignments.early.schedule[['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][date.getDay()]]}
              </div>
            </div>
          )}
          {assignments.day && (
            <div className="border-l-4 border-green-500 pl-3 py-2 bg-green-50 rounded">
              <div className="font-semibold text-green-900">☀️ Day Shift (08:00-18:00)</div>
              <div className="text-sm text-green-800">{assignments.day.name}</div>
              <div className="text-xs text-green-600">{assignments.day.email}</div>
              <div className="text-xs text-green-700 mt-1">
                Hours: {assignments.day.schedule[['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][date.getDay()]]}
              </div>
            </div>
          )}
          {assignments.evening && (
            <div className="border-l-4 border-purple-500 pl-3 py-2 bg-purple-50 rounded">
              <div className="font-semibold text-purple-900">🌆 Evening Shift (15:00-00:00)</div>
              <div className="text-sm text-purple-800">{assignments.evening.name}</div>
              <div className="text-xs text-purple-600">{assignments.evening.email}</div>
              <div className="text-xs text-purple-700 mt-1">
                Hours: {assignments.evening.schedule[['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][date.getDay()]]}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Users className="w-7 h-7 text-blue-600" />
            NOC Incident Watch Rotation
          </h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setCurrentMonth(Math.max(0, currentMonth - 1))}
              disabled={currentMonth === 0}
              className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="text-xl font-semibold text-gray-700 min-w-48 text-center">
              {calendarData.monthName} {calendarData.year}
            </span>
            <button
              onClick={() => setCurrentMonth(Math.min(2, currentMonth + 1))}
              disabled={currentMonth === 2}
              className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="mb-4 flex gap-4 text-xs flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-indigo-100 border border-indigo-300 rounded"></div>
            <span>🌙 Night (00:00-10:00)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-amber-100 border border-amber-300 rounded"></div>
            <span>🌅 Early (05:00-09:00)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
            <span>☀️ Day (08:00-18:00)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-100 border border-purple-300 rounded"></div>
            <span>🌆 Evening (15:00-00:00)</span>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-0 border border-gray-300 rounded-lg overflow-hidden">
          {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(day => (
            <div key={day} className="bg-gray-100 p-2 text-center font-semibold text-sm text-gray-700 border-b border-gray-300">
              {day}
            </div>
          ))}
          {renderCalendar()}
        </div>

        {renderSelectedDateDetails()}

        <div className="mt-6 text-sm text-gray-600 bg-blue-50 p-4 rounded-lg">
          <p className="font-semibold mb-2">📋 Rotation Logic:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Engineers are automatically rotated within their assigned shift</li>
            <li>Only available engineers (not on OFF days) are assigned</li>
            <li>Single-threaded shifts (weekends) automatically assign the only available engineer</li>
            <li>Click any date to see full assignment details including contact info and exact hours</li>
            <li>Rotation ensures fair distribution across all available team members</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NOCRotationCalendar;