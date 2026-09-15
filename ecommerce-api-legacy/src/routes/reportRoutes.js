// Financial report HTTP layer.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (reportController) => {
  const router = express.Router();

  router.get(
    '/api/admin/financial-report',
    asyncHandler(async (req, res) => {
      res.json(await reportController.financialReport());
    })
  );

  return router;
};
