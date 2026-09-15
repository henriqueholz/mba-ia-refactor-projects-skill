// User HTTP layer.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (userController) => {
  const router = express.Router();

  router.delete(
    '/api/users/:id',
    asyncHandler(async (req, res) => {
      res.json(await userController.deleteUser(req.params.id));
    })
  );

  return router;
};
