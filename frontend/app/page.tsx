'use client';

import { useState, useEffect } from 'react';

interface Task {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  created_at: string;
}

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks');
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (error) {
      console.error('Lỗi lấy danh sách task:', error);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const addTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setIsLoading(true);
    try {
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description }),
      });
      if (res.ok) {
        setTitle('');
        setDescription('');
        await fetchTasks();
      }
    } catch (error) {
      console.error('Lỗi tạo task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTask = async (taskId: string, completed: boolean) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed }),
      });
      if (res.ok) {
        await fetchTasks();
      }
    } catch (error) {
      console.error('Lỗi cập nhật task:', error);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        await fetchTasks();
      }
    } catch (error) {
      console.error('Lỗi xóa task:', error);
    }
  };

  return (
    <main className="max-w-2xl mx-auto p-6 font-sans">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Quản lý Công việc</h1>

      {/* Form thêm Task */}
      <form onSubmit={addTask} className="mb-8 p-4 border border-gray-200 rounded-lg bg-gray-50 shadow-sm">
        <h2 className="text-lg font-semibold mb-3 text-gray-700">Thêm công việc mới</h2>
        <div className="mb-3">
          <label className="block text-sm font-medium mb-1 text-gray-600">Tiêu đề *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-blue-500"
            placeholder="Nhập tên công việc..."
            required
          />
        </div>
        <div className="mb-3">
          <label className="block text-sm font-medium mb-1 text-gray-600">Mô tả</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-blue-500"
            rows={2}
            placeholder="Mô tả chi tiết (tùy chọn)..."
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {isLoading ? 'Đang thêm...' : 'Thêm công việc'}
        </button>
      </form>

      {/* Danh sách Task */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Danh sách công việc</h2>
        {tasks.length === 0 ? (
          <p className="text-gray-500 italic">Chưa có công việc nào.</p>
        ) : (
          <ul className="space-y-3">
            {tasks.map((task) => (
              <li
                key={task.id}
                className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm flex justify-between items-center"
              >
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={(e) => toggleTask(task.id, e.target.checked)}
                    className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <div>
                    <h3
                      className={`font-medium ${
                        task.completed ? 'line-through text-gray-400' : 'text-gray-800'
                      }`}
                    >
                      {task.title}
                    </h3>
                    {task.description && (
                      <p className="text-sm text-gray-500">{task.description}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(task.created_at).toLocaleString('vi-VN')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="text-red-500 hover:text-red-700 font-medium text-sm px-2 py-1 transition"
                >
                  Xóa
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}