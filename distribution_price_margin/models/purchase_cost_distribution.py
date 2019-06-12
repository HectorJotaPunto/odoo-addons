from odoo import models, fields, exceptions, api, _


class PurchaseCostDistribution(models.Model):
    _inherit = "purchase.cost.distribution"
    
    cost_lines = fields.One2many(readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]})
    benefit_margin = fields.Float(string='Margin %', readonly=True, states={'draft': [('readonly', False)], 'calculated': [('readonly', False)]}, default=-1, help="If the margin is less than 0, it won't be applied")

    @api.multi
    def action_calculate(self):
        super(PurchaseCostDistribution, self).action_calculate()
        for distribution in self:
            for line in distribution.cost_lines:
                if line.benefit_margin >= 0:
                    if self.env.ref('distribution_price_margin.group_margin_calculation_type') in self.env['res.users'].browse([self._uid]).groups_id:
                        line.benefit_price = line.standard_price_new / (1 - (line.benefit_margin / 100))
                    else:
                        line.benefit_price = line.standard_price_new + (line.standard_price_new * (line.benefit_margin / 100))
                else:
                    line.benefit_price = 0
        return True
    
    @api.multi
    def set_margin(self):
        for distribution in self:
            for line in distribution.cost_lines:
                line.benefit_margin = distribution.benefit_margin
    
    @api.one
    def action_done(self):
        for line in self.cost_lines:
            if line.benefit_price > 0:
                line.product_id.lst_price = line.benefit_price
        super(PurchaseCostDistribution, self).action_done()

    
class PurchaseCostDistributionLine(models.Model):
    _inherit = "purchase.cost.distribution.line"
    
    state = fields.Selection(readonly=True, related="distribution.state")
    benefit_margin = fields.Float(string='Margin %', readonly=False, default=-1)
    benefit_price = fields.Float(string='Sale Price', help=("If the value is 0 or negative, the sale price won't be changed"))
    old_sale_price = fields.Float(related="product_id.lst_price", readonly=True)
    
    @api.onchange('benefit_price')
    def onchange_benefit_price(self):
        if self.benefit_price >= 0:
            try:
                if self.env.ref('distribution_price_margin.group_margin_calculation_type') in self.env['res.users'].browse([self._uid]).groups_id:
                    self.benefit_margin = (1 - (self.standard_price_new / self.benefit_price)) * 100
                else:
                    self.benefit_margin = ((self.benefit_price - self.standard_price_new) / self.standard_price_new) * 100
            except:
                self.benefit_margin = -1
        else:
            self.benefit_margin = -1
    
    @api.onchange('benefit_margin')
    def onchange_benefit_margin(self):
        if self.benefit_margin >= 0:
            try:
                if self.env.ref('distribution_price_margin.group_margin_calculation_type') in self.env['res.users'].browse([self._uid]).groups_id:
                    self.benefit_price = self.standard_price_new / (1 - (self.benefit_margin / 100))
                else:
                    self.benefit_price = self.standard_price_new + (self.standard_price_new * (self.benefit_margin / 100))
            except:
                self.benefit_price = 0
        else:
            self.benefit_price = 0

