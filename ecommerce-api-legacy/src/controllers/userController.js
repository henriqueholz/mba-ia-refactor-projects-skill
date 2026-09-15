// User business logic.
const { AppError } = require('../errors');

class UserController {
  constructor({ userModel }) {
    this.users = userModel;
  }

  async deleteUser(id) {
    const removed = await this.users.deleteWithDependencies(id);
    if (!removed) throw new AppError('Usuário não encontrado', 404);
    // Enrollments and payments are cleaned up in the same transaction.
    return { msg: 'Usuário e dados relacionados removidos' };
  }
}

module.exports = UserController;
