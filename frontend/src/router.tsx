// SPDX-License-Identifier: AGPL-3.0-or-later
import { createBrowserRouter } from 'react-router';

import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { NonTrovata } from './pages/NonTrovata';

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: '*', element: <NonTrovata /> },
    ],
  },
]);
